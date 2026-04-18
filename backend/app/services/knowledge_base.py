import logging

from app.core.logging import LogCategory, LogLayer, AppLoggerAdapter, extra_
from .vector_db import ChunkCreationService, ChromaVectorIndexService

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.AGENT,
        "component": __name__,
    },
)


class KnowledgeBaseService:
    def __init__(self, which="chroma"):
        logger.info(
            "Initializing KnowledgeBaseService",
            extra=extra_(operation="kb_init", status="start", vector_db=which),
        )
        self.chunk_creator =ChunkCreationService()

        match which:
            case "chroma":
                self.vector_index = ChromaVectorIndexService()
                logger.debug(
                    "Using ChromaDB as vector index",
                    extra=extra_(
                        operation="kb_init", 
                        status="in_progress", 
                        vector_db="chroma"
                    ),
                )

            case _:
                self.vector_index = ChromaVectorIndexService()
                logger.warning(
                    "Unknown vector DB type, defaulting to ChromaDB",
                    extra=extra_(operation="kb_init", status="warning", vector_db=which),
                )

        logger.info(
            "KnowledgeBaseService initialized",
            extra=extra_(operation="kb_init", status="success", vector_db=which),
        )

    async def create_and_upload_chunks(
        self, filepath: str, chunk_size: int, overlapping: int
    ):
        logger.info(
            "Creating and uploading chunks",
            extra=extra_(
                operation="kb_upload",
                status="start",
                filepath=filepath,
                chunk_size=chunk_size,
                overlap=overlapping,
            ),
        )
        try:
            logger.debug(
                "Creating chunks from file",
                extra=extra_(operation="kb_upload", status="in_progress", filepath=filepath),
            )
            chunks = self.chunk_creator.create_chunks(
                filepath=filepath,
                chunk_size=chunk_size,
                overlapping=overlapping
            )
            logger.info(
                "Chunks created",
                extra=extra_(
                    operation="kb_upload",
                    status="in_progress",
                    filepath=filepath,
                    chunks=len(chunks),
                ),
            )
            
            logger.debug(
                "Updating vector index with chunks",
                extra=extra_(
                    operation="kb_upload",
                    status="in_progress",
                    filepath=filepath,
                    chunks=len(chunks),
                ),
            )
            await self.vector_index.update_index(chunks=chunks, update_source=filepath)
            logger.info(
                "Chunks uploaded to vector index",
                extra=extra_(
                    operation="kb_upload",
                    status="success",
                    filepath=filepath,
                    chunks=len(chunks),
                ),
            )
        except Exception as e:
            logger.exception(
                "KB upload failed",
                extra=extra_(
                    operation="kb_upload",
                    status="failure",
                    filepath=filepath,
                    error_type=type(e).__name__,
                ),
            )
            raise

    async def query_index(self, query:str, rerank:bool=False):
        logger.debug(
            "Querying knowledge base",
            extra=extra_(
                operation="kb_query",
                status="start",
                query_preview=(query or "")[:120],
                rerank=rerank,
            ),
        )
        try:
            knowledge = await self.vector_index.query_index(
                text_query=query,
                rerank=rerank
            )
            logger.info(
                "Knowledge base query completed",
                extra=extra_(
                    operation="kb_query",
                    status="success",
                    result_len=len(knowledge) if knowledge else 0,
                    rerank=rerank,
                ),
            )
            return knowledge
        except Exception as e:
            logger.exception(
                "Knowledge base query failed",
                extra=extra_(
                    operation="kb_query",
                    status="failure",
                    rerank=rerank,
                    error_type=type(e).__name__,
                ),
            )
            raise
    
    async def close(self):
        logger.debug(
            "Closing knowledge base service",
            extra=extra_(operation="kb_close", status="start"),
        )
        try:
            await self.vector_index.close()
            logger.info(
                "Knowledge base service closed successfully",
                extra=extra_(operation="kb_close", status="success"),
            )
        except Exception as e:
            logger.exception(
                "Error closing knowledge base service",
                extra=extra_(
                    operation="kb_close",
                    status="failure",
                    error_type=type(e).__name__,
                ),
            )
            raise
