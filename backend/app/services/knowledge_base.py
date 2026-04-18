import logging

from app.core.logging import LogCategory, LogLayer, AppLoggerAdapter
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
        logger.info(f"Initializing KnowledgeBaseService with vector DB: {which}")
        self.chunk_creator =ChunkCreationService()

        match which:
            case "chroma":
                self.vector_index = ChromaVectorIndexService()
                logger.debug("Using ChromaDB as vector index")

            case _:
                self.vector_index = ChromaVectorIndexService()
                logger.warning(
                    f"Unknown vector DB type '{which}', defaulting to ChromaDB"
                )

        logger.info(f"KnowledgeBaseService initialized with {which}")

    async def create_and_upload_chunks(
        self, filepath: str, chunk_size: int, overlapping: int
    ):
        logger.info((
                f"Creating and uploading chunks from file: {filepath}, "
                f"chunk_size: {chunk_size}, overlap: {overlapping}"
            ))
        try:
            logger.debug("Creating chunks from file")
            chunks = self.chunk_creator.create_chunks(
                filepath=filepath,
                chunk_size=chunk_size,
                overlapping=overlapping
            )
            logger.info(f"Created {len(chunks)} chunks from file {filepath}")
            
            logger.debug("Updating vector index with chunks")
            await self.vector_index.update_index(chunks=chunks, update_source=filepath)
            logger.info(f"Successfully uploaded {len(chunks)} chunks to vector index")
        except Exception as e:
            logger.exception((
                f"Error creating and uploading chunks from {filepath}: {e}"
            ), exc_info=True)
            raise

    async def query_index(self, query:str, rerank:bool=False):
        logger.debug((
            f"Querying knowledge base - query: "
            f"{query[:100] if len(query) > 100 else query}, rerank: {rerank}"
        ))
        try:
            knowledge = await self.vector_index.query_index(
                text_query=query,
                rerank=rerank
            )
            logger.info((
                f"Knowledge base query completed, result length: "
                "{len(knowledge) if knowledge else 0}"
            ))
            return knowledge
        except Exception as e:
            logger.exception(f"Error querying knowledge base: {e}", exc_info=True)
            raise
    
    async def close(self):
        logger.debug("Closing knowledge base service")
        try:
            await self.vector_index.close()
            logger.info("Knowledge base service closed successfully")
        except Exception as e:
            logger.exception(
                f"Error closing knowledge base service: {e}", 
                exc_info=True
            )
            raise