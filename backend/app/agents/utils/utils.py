from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import envs


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
            model = ChatOpenAI(
                api_key=envs.OPENAI_API_KEY,
                temperature=temperature,
                model=model,
                streaming=streaming
            )

        case "google":
            model = ChatGoogleGenerativeAI(
                api_key=envs.GOOGLE_API_KEY,
                model=model,
                streaming=streaming,
                temperature=temperature
            )

        case "groq":
            model = ChatGroq(
                api_key=envs.GROQ_API_KEY,
                temperature=temperature,
                model=model,
                streaming=streaming,
            )

        case _:
            model = ChatOpenAI(
                api_key=envs.OPENAI_API_KEY,
                temperature=temperature,
                streaming=streaming,
                model="gpt-4o-2024-08-06"
            )

    return model
