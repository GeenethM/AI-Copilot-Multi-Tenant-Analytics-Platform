from state.agent_state import AgentState


def route_after_agent(state: AgentState) -> str:
    """
    Routing function called after every agent turn.

    Inspects the last message and decides where the graph goes next:
        - 'tools' → the agent wants to call one or more tools
        - 'end'   → the agent has produced a final answer

    LangGraph uses the returned string to pick the next node via
    add_conditional_edges() in agent_graph.py.
    """
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "end"
