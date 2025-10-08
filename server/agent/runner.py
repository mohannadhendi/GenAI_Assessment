import json
import uuid
from datetime import datetime
from server.agent.chains.library_agent import build_library_agent
from server.db import SessionLocal
from server.models.message import Message
from server.models.tool_call import ToolCall
from server.config import get_settings
from openai import OpenAI
from langchain.callbacks.base import BaseCallbackHandler



def safe_json_dumps(obj):
    """Safely convert objects (like datetime) into JSON serializable format."""
    def default(o):
        import datetime
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        return str(o)
    return json.dumps(obj, ensure_ascii=False, default=default)


def log_message(session_id: str, role: str, content: str):
    """Store user or assistant messages."""
    db = SessionLocal()
    try:
        msg = Message(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
    finally:
        db.close()


def log_tool_call(session_id: str, name: str, args: dict, result: dict):
    """Store tool execution info in the database."""
    db = SessionLocal()
    try:
        db.add(
            ToolCall(
                session_id=session_id,
                name=name,
                args_json=safe_json_dumps(args),
                result_json=safe_json_dumps(result),
                created_at=datetime.utcnow(),
            )
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to log tool call: {e}")
    finally:
        db.close()


def run_agent_query(user_query: str, session_id: str = None):
    """Run the agent, record all tool invocations, and generate a summary."""
    if not session_id:
        session_id = str(uuid.uuid4())

    log_message(session_id, "user", user_query)
    agent = build_library_agent(verbose=True)


    class ToolLogger(BaseCallbackHandler):
        def on_tool_start(self, serialized, input_str, **kwargs):
            name = serialized.get("name", "unknown")
            print(f"[TOOL START] {name} → {input_str}")
            log_tool_call(session_id, name, {"input": input_str}, {"status": "started"})

        def on_tool_end(self, output, **kwargs):
            print(f"[TOOL END] → {output}")
            log_tool_call(session_id, "tool_result", {}, {"output": output})

    #Instead of agent.callback_manager, pass callbacks directly
    callbacks = [ToolLogger()]

    try:
        response_dict = agent.invoke(
            {"input": user_query, "chat_history": []},
            config={"callbacks": callbacks}
        )
        response = response_dict.get("output", response_dict)
    except Exception as e:
        log_message(session_id, "assistant", f"Error: {e}")
        return {"session_id": session_id, "error": str(e)}

    # Parse structured response
    if isinstance(response, str):
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            parsed = {"text": response}
    else:
        parsed = response

    # Summarize the output for the chat UI
    settings = get_settings()
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    summary_prompt = f"""
    User query: "{user_query}"
    Structured response: {safe_json_dumps(parsed)}

    Summarize the result in 1–2 clear sentences for the chat interface.
    """

    try:
        summary_completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a concise assistant summarizing the AI agent's output."},
                {"role": "user", "content": summary_prompt},
            ],
        )
        summary_text = summary_completion.choices[0].message.content.strip()
    except Exception as e:
        summary_text = f"Summary unavailable: {e}"

    # Log assistant response + summary
    log_message(session_id, "assistant", safe_json_dumps(parsed))
    log_tool_call(session_id, "agent_summary",
                  {"query": user_query},
                  {"result": parsed, "summary": summary_text})

    return {
        "session_id": session_id,
        "tool": "multi_tool_chain",
        "args": {},
        "response": parsed,
        "summary": summary_text
    }
