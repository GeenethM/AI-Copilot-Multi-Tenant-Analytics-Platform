from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from nodes.data_nodes import ALL_TOOLS, agent_node
from nodes.decision_nodes import route_after_agent
from state.agent_state import AgentState


def build_agent_graph():
    """
    Builds and compiles the LangGraph agent workflow.

    Graph flow:
        [start]
           │
           ▼
         agent  ──── has tool calls? ──── yes ──► tools
           ▲                                        │
           │                no                      │
           ▼                                        │
          END ◄───────────────────────────────────┘
              (tools always loop back to agent)

    The agent keeps looping until it has a final answer with no tool calls.
    """
    workflow = StateGraph(AgentState)

    # --- Nodes ---
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))

    # --- Entry point ---
    workflow.set_entry_point("agent")

    # --- Edges ---
    # After the agent runs: go to tools OR end, based on routing logic
    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # After tools run: always go back to the agent for the next reasoning step
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# Module-level compiled graph — import this wherever you need to run the agent
agent_graph = build_agent_graph()
