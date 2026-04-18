from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
import logging

from app.core.config import envs
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.services import KnowledgeBaseService

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.TOOL,
        "category": LogCategory.TOOL_EXECUTION,
        "component": __name__,
    },
)


@tool("search_knowledge_base", parse_docstring=True)
async def search_knowledge_base(query: str, config: RunnableConfig) -> dict:
    """Search internal knowledge base for policies, FAQs, and guidelines.

    This tool is used for answering general questions such as return policies,
    warranty rules, and process explanations.

    Args:
        query: Natural language query describing what to search for.

    Returns:
        dict: Search result containing relevant policy or FAQ information.
            Example:
            {
                "answer": "Electronics have a 30-day return window...",
                "source": "return_policy_v2"
            }
    """
    kb_service = KnowledgeBaseService(which=envs.WHICH_KNOWLEDGE_BASE)
    try:
        logger.debug(
            "Searching knowledge base",
            extra=extra_(
                operation="search_knowledge_base",
                status="start",
                query_preview=(query or "")[:120],
            ),
        )
        knowledge = await kb_service.query_index(query=query, rerank=False)
        logger.info(
            "Knowledge base search completed",
            extra=extra_(operation="search_knowledge_base", status="success"),
        )
        return knowledge
    except Exception as e:
        logger.exception(
            "Knowledge base search failed",
            extra=extra_(
                operation="search_knowledge_base",
                status="failure",
                error_type=type(e).__name__,
            ),
        )
        raise
