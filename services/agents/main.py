"""
AI Agent Service — Entry Point
===============================
This is the main file you run to interact with the agent.

Usage:
    # From the services/agents/ directory:
    python main.py

    # Or run a single task directly:
    python main.py "Summarize my sales dataset"
"""

import sys

from langchain_core.messages import HumanMessage

from graphs.agent_graph import agent_graph


def run_agent(task: str) -> str:
    """
    Send a task to the agent and return its final text response.

    Args:
        task: A natural language description of what you want the agent to do.

    Returns:
        The agent's final response as a plain string.
    """
    initial_state = {
        "messages": [HumanMessage(content=task)],
        "task": task,
        "data_context": None,
        "results": None,
    }

    final_state = agent_graph.invoke(initial_state)
    return final_state["messages"][-1].content


if __name__ == "__main__":
    # Allow a one-off task from the command line: python main.py "my task"
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        print(f"\nAgent: {run_agent(task)}\n")
        sys.exit(0)

    # Otherwise, run an interactive loop
    print("AI Agent Service ready.")
    print("Type your task and press Enter. Type 'quit' to exit.\n")

    while True:
        try:
            task = input("Task > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not task:
            continue

        if task.lower() in ("quit", "exit", "q"):
            break

        print(f"\nAgent: {run_agent(task)}\n")
