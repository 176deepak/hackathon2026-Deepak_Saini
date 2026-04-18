from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import envs
import logging
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.AGENT,
        "category": LogCategory.AGENT,
        "component": __name__,
    },
)


def get_chat_llm(
    provider: str,
    model: str,
    streaming: bool = False,
    temperature: float = 0.5
) -> BaseChatModel:
    """Get llm by given llm provider

    Args:
        provider: LLM provider(Google, OpenAI, Claude etc.)
        model: Respective model name
        streaming: Should streaming model?
        temperature: Model creativity level([0, 2])

    Returns:
        llm: ChatModel(BaseChatModel)
    """
    match provider:
        case "openai":
            logger.debug(
                "Creating OpenAI chat model",
                extra=extra_(operation="get_chat_llm", status="start", provider="openai", model=model),
            )
            model = ChatOpenAI(
                api_key=envs.OPENAI_API_KEY,
                temperature=temperature,
                model=model,
                streaming=streaming
            )

        case "google":
            logger.debug(
                "Creating Google chat model",
                extra=extra_(operation="get_chat_llm", status="start", provider="google", model=model),
            )
            model = ChatGoogleGenerativeAI(
                api_key=envs.GOOGLE_API_KEY,
                model=model,
                streaming=streaming,
                temperature=temperature
            )

        case "groq":
            logger.debug(
                "Creating Groq chat model",
                extra=extra_(operation="get_chat_llm", status="start", provider="groq", model=model),
            )
            model = ChatGroq(
                api_key=envs.GROQ_API_KEY,
                temperature=temperature,
                model=model,
                streaming=streaming,
            )

        case _:
            logger.warning(
                "Unknown LLM provider, defaulting to OpenAI",
                extra=extra_(operation="get_chat_llm", status="warning", provider=provider),
            )
            model = ChatOpenAI(
                api_key=envs.OPENAI_API_KEY,
                temperature=temperature,
                streaming=streaming,
                model="gpt-4o-2024-08-06"
            )

    logger.info(
        "Chat model created",
        extra=extra_(
            operation="get_chat_llm",
            status="success",
            provider=provider,
            streaming=streaming,
            temperature=temperature,
        ),
    )
    return model
