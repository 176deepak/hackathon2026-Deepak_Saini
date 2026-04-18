from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.core.config import envs
from app.services import KnowledgeBaseService


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
        knowledge = await kb_service.query_index(query=query, rerank=False)
        
        return knowledge
    except Exception as e:
        raise