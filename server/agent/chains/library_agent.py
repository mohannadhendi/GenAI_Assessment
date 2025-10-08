from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from server.agent.tools.find_books_tool import FindBooksTool
from server.agent.tools.restock_book_tool import RestockBookTool
from server.agent.tools.create_order_tool import CreateOrderTool
from server.agent.tools.order_status_tool import OrderStatusTool
from server.agent.tools.update_price_tool import UpdatePriceTool
from server.agent.tools.inventory_summary_tool import InventorySummaryTool
from server.config import get_settings


def load_system_prompt() -> str:
    """Load system prompt text safely."""
    try:
        with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "You are a helpful AI Library Assistant that manages books, customers, and orders."


def build_library_agent(verbose: bool = True):
    settings = get_settings()

    llm = ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0,
        openai_api_key=settings.OPENAI_API_KEY,
    )

    tools = [
        FindBooksTool(),
        RestockBookTool(),
        CreateOrderTool(),
        OrderStatusTool(),
        UpdatePriceTool(),
        InventorySummaryTool(),
    ]

    # --- ✅ Manual ReAct-compatible prompt template ---
    react_template = """Answer the following questions as best you can.
    You have access to the following tools:

    {tools}

    Use this format:

    Question: the input question you must answer
    Thought: think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Observation repeats as needed)
    Thought: I now know the final answer
    Final Answer: the final answer to the original question

    Begin!

    Question: {input}
    {agent_scratchpad}
    """

    prompt = PromptTemplate(
        input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
        template=react_template,
    )

    # Build multi-step ReAct agent
    agent = create_react_agent(llm, tools, prompt)

    # Enable automatic looping & error handling
    return AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=5,
        early_stopping_method="force",
    )
