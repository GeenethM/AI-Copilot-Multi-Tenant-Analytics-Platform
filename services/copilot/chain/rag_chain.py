"""
rag_chain.py
────────────
Assembles the full RAG pipeline:
    retrieve relevant chunks → format them into a prompt → call the LLM

The chain is built using LangChain Expression Language (LCEL), which means
every step is composable with the | pipe operator.

Flow for a single question:
    question
        │
        ▼
    retriever.invoke(question)          ← semantic search in ChromaDB
        │
        ▼
    format_context(chunks)              ← join chunk texts into one string
        │
        ▼
    COPILOT_PROMPT.format(context, ...) ← build the full LLM prompt
        │
        ▼
    LLM.invoke(prompt)                  ← generate the answer
        │
        ▼
    StrOutputParser()                   ← extract plain string from response
"""

from typing import List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from chain.prompts import COPILOT_PROMPT
from config.llm_factory import get_llm
from retriever.retriever import get_retriever


def _format_context(docs: List[Document]) -> str:
    """
    Joins retrieved document chunks into a single context string for the prompt.
    Each chunk is separated by a divider so the LLM can distinguish between them.
    """
    if not docs:
        return "No relevant documents found."

    sections = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source_file", "unknown")
        sections.append(f"[Chunk {i} — {source}]\n{doc.page_content}")

    return "\n\n".join(sections)


def build_rag_chain(tenant_id: str):
    """
    Build and return a RAG chain for a specific tenant.

    The returned chain accepts a dict with keys:
        - 'question':     The user's current question (str)
        - 'chat_history': Previous messages in this session (list, can be empty)

    And returns a plain string answer.

    Args:
        tenant_id: Used to load the correct tenant-scoped ChromaDB collection.

    Returns:
        A LangChain Runnable chain.
    """
    retriever = get_retriever(tenant_id)
    llm = get_llm()

    chain = (
        {
            # Retrieve relevant chunks based on the question
            "context": (lambda x: x["question"]) | retriever | _format_context,
            # Pass through the question and chat history unchanged
            "question": RunnablePassthrough() | (lambda x: x["question"]),
            "chat_history": RunnablePassthrough() | (lambda x: x.get("chat_history", [])),
        }
        | COPILOT_PROMPT
        | llm
        | StrOutputParser()
    )

    return chain


def ask(tenant_id: str, question: str, chat_history: list | None = None) -> str:
    """
    Convenience function: ask a single question and get a plain string answer.

    Args:
        tenant_id:    The tenant whose documents to search.
        question:     The user's natural language question.
        chat_history: Optional list of previous (human, ai) message tuples
                      for multi-turn conversation memory.

    Returns:
        The AI Copilot's answer as a plain string.
    """
    chain = build_rag_chain(tenant_id)
    return chain.invoke(
        {
            "question": question,
            "chat_history": chat_history or [],
        }
    )
