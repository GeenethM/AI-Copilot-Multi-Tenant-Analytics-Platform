from langchain_core.messages import SystemMessage

from config.llm_factory import get_llm
from prompts.templates import AGENT_SYSTEM_PROMPT
from state.agent_state import AgentState
from tools.data_tools import query_business_data, summarize_dataset
from tools.task_tools import create_report, schedule_task, send_alert

# All tools available to the agent — add new tools here as the platform grows
ALL_TOOLS = [
    query_business_data,
    summarize_dataset,
    send_alert,
    create_report,
    schedule_task,
]


def agent_node(state: AgentState) -> dict:
    """
    The main agent node.

    The LLM sees the full conversation history, reasons about what to do,
    and either calls a tool or returns a final answer.
    """
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    messages = list(state["messages"])

    # Prepend the system prompt on the very first turn
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}
