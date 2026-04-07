import operator
from typing import Annotated, Any, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Shared state that flows between all nodes in the agent graph.
    Think of this as the agent's working memory for a single task run.

    Every node receives this dict and can return updated fields.
    The 'messages' field uses operator.add so each node appends — not overwrites.
    """

    # Full conversation history for this run (nodes append to this list)
    messages: Annotated[List[BaseMessage], operator.add]

    # The original task string submitted by the user
    task: str

    # Optional: business data context pre-loaded for this task
    data_context: Optional[str]

    # Optional: structured results produced by the agent
    results: Optional[Any]
