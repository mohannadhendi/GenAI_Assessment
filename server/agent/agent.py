import json
from openai import OpenAI
from server.db import SessionLocal
from server.tools import (
    find_books,
    create_order,
    restock_book,
    update_price,
    order_status,
    inventory_summary,
)
from server.config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def load_system_prompt() -> str:
    """Read the system prompt that defines how GPT-4 behaves."""
    with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

def safe_json_dumps(obj):
    """Safely convert objects (like datetime) into JSON serializable format."""
    def default(o):
        import datetime
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        return str(o)
    return json.dumps(obj, ensure_ascii=False, default=default)





def process_user_message(message: str):
    """
    Understand the user's message, decide which tool to use,
    execute it, and return both structured and natural replies.
    Supports automatic chaining (for example, find_books → create_order).
    """
    db = SessionLocal()
    system_prompt = load_system_prompt()

    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        )
        parsed = json.loads(completion.choices[0].message.content)
        tool_name = parsed.get("tool")
        args = parsed.get("args", {})
        print(f"GPT selected tool: {tool_name}, args: {args}")

    except Exception as e:
        db.close()
        return {"error": f"Could not interpret your request. ({e})"}

    tool_map = {
        "find_books": lambda params: find_books(db, **params),
        "create_order": lambda params: create_order(db, **params),
        "restock_book": lambda params: restock_book(db, **params),
        "update_price": lambda params: update_price(db, **params),
        "order_status": lambda params: order_status(db, **params),
        "inventory_summary": lambda params: inventory_summary(db, **params),
    }

    if tool_name not in tool_map:
        db.close()
        return {"error": f"Unknown tool name: {tool_name}"}

    try:
        result = tool_map[tool_name](args)
        print(f"Executed {tool_name}, result count: {len(result) if isinstance(result, list) else 1}")
    except Exception as e:
        db.rollback()
        db.close()
        return {"error": f"Error while executing {tool_name}: {e}"}

    if tool_name == "find_books" and result:
        found_isbns = [b["isbn"] for b in result]
        titles = [b["title"] for b in result]
        print(f"Found books: {titles} (ISBNs: {found_isbns})")

        if any(w in message.lower() for w in ["order", "buy", "purchase", "restock", "add", "increase", "price"]):
            followup_instruction = (
                f"The user said: '{message}'.\n"
                f"The following books were found: {list(zip(titles, found_isbns))}.\n"
                f"Now you must output only one valid JSON object describing the next tool call.\n"
                f"Use the correct tool based on the intent:\n"
                f"- For 'order' → use create_order\n"
                f"- For 'restock' → use restock_book\n"
                f"- For 'price' → use update_price\n"
                f"Example output:\n"
                f'{{\"tool\": \"create_order\", \"args\": {{\"customer_id\": 2, \"items\": [{{\"isbn\": \"{found_isbns[0]}\", \"qty\": 2}}]}}}}'
            )

            try:
                followup = client.chat.completions.create(
                    model="gpt-4-turbo",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": followup_instruction},
                    ],
                )
                next_parsed = json.loads(followup.choices[0].message.content)
                next_tool = next_parsed.get("tool")
                next_args = next_parsed.get("args", {})
                print(f"Auto-chaining to: {next_tool}, args: {next_args}")

                if next_tool in tool_map:
                    result = tool_map[next_tool](next_args)
                    tool_name = next_tool
                    args = next_args
            except Exception as e:
                print(f"Secondary GPT step failed: {e}")

    db.close()

    summary_prompt = f"""
    The user asked: "{message}"
    Tool used: {tool_name}
    Result: {safe_json_dumps(result)}
    Write a short, friendly summary for the user.
    """

    try:
        summary_completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly assistant summarizing results."},
                {"role": "user", "content": summary_prompt},
            ],
        )
        summary = summary_completion.choices[0].message.content.strip()
    except Exception as e:
        summary = f"Tool '{tool_name}' executed successfully, but summary generation failed ({e})."

    return {
        "tool": tool_name,
        "args": args,
        "result": result,
        "summary": summary,
    }
