from langchain_core.language_models import BaseChatModel

from config.settings import get_settings


def get_llm() -> BaseChatModel:
    """
    Returns the configured LLM based on LLM_PROVIDER in your .env file.
    Swap providers by changing LLM_PROVIDER — no code changes needed.
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


def get_embedding_model():
    """
    Returns the configured embedding model.
    Embeddings turn text into vectors so ChromaDB can search by meaning.
    """
    settings = get_settings()

    if settings.embedding_provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key or None,
        )

    if settings.embedding_provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=settings.huggingface_embedding_model)

    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER: '{settings.embedding_provider}'. "
        "Valid options are: openai, huggingface"
    )
