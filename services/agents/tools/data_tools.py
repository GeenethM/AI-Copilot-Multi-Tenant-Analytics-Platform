from langchain_core.tools import tool


@tool
def query_business_data(query: str, dataset: str = "sales") -> str:
    """
    Query business data uploaded by a tenant.

    Args:
        query:   Natural language question about the data.
                 Example: "What were total sales in Q1?"
        dataset: Which dataset to query — e.g. 'sales', 'operations', 'finance'.
                 Defaults to 'sales'.

    Returns:
        Query results as a plain string.
    """
    # Placeholder — will connect to the multi-tenant PostgreSQL layer in a later phase.
    return (
        f"[Placeholder] Query '{query}' on dataset '{dataset}' returned no results. "
        "The database layer has not been connected yet."
    )


@tool
def summarize_dataset(dataset: str) -> str:
    """
    Return a high-level summary of an uploaded business dataset.

    Args:
        dataset: Name of the dataset to summarize.
                 Example: 'sales', 'inventory', 'hr'

    Returns:
        Summary statistics and key metrics as a string.
    """
    # Placeholder — will connect to data layer in a later phase.
    return (
        f"[Placeholder] Dataset '{dataset}' summary: "
        "No data connected yet. Check back after the database layer is built."
    )
