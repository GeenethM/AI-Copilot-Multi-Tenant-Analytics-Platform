from langchain_core.tools import tool


@tool
def send_alert(message: str, channel: str = "email") -> str:
    """
    Send a business alert or notification.

    Args:
        message: The alert message content.
        channel: Delivery channel — 'email', 'slack', or 'sms'. Defaults to 'email'.

    Returns:
        Confirmation string.
    """
    # Placeholder — will integrate with a notification service in a later phase.
    return (
        f"[Placeholder] Alert queued via {channel}: '{message}'. "
        "Notification service not connected yet."
    )


@tool
def create_report(title: str, content: str) -> str:
    """
    Generate and save a business intelligence report.

    Args:
        title:   The report title.
        content: The report body — typically a data summary or agent analysis.

    Returns:
        Confirmation string with a placeholder report ID.
    """
    # Placeholder — will save to storage layer in a later phase.
    return (
        f"[Placeholder] Report '{title}' created. "
        "Storage layer not connected yet."
    )


@tool
def schedule_task(task_name: str, schedule: str, parameters: str = "") -> str:
    """
    Schedule a recurring automated task.

    Args:
        task_name:  Name identifying the task (e.g. 'weekly_sales_report').
        schedule:   Human-readable schedule string (e.g. 'every Monday at 9am').
        parameters: Optional extra parameters for the task as a JSON-like string.

    Returns:
        Confirmation string with a placeholder task ID.
    """
    # Placeholder — will integrate with a task scheduler in a later phase.
    return (
        f"[Placeholder] Task '{task_name}' scheduled for '{schedule}'. "
        "Task scheduler not connected yet."
    )
