from langchain_core.language_models import BaseChatModel

from config.settings import get_settings


def get_llm() -> BaseChatModel:
    """
    Returns the configured LLM based on LLM_PROVIDER in your .env file.

    To swap providers, just change LLM_PROVIDER in .env — no code changes needed.
    Each provider's library is imported lazily so you only need to install the one
    you're actually using.
    """
    settings = get_settings()

    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.model_name,
            temperature=settings.temperature,
            api_key=settings.openai_api_key or None,
        )

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.model_name,
            temperature=settings.temperature,
            api_key=settings.anthropic_api_key or None,
        )

    if settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.model_name,
            temperature=settings.temperature,
            google_api_key=settings.google_api_key or None,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER: '{settings.llm_provider}'. "
        "Valid options are: openai, anthropic, google"
    )
