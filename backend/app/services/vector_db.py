import logging
from pathlib import Path
from langchain_community.document_loaders import (
    TextLoader,
    PyMuPDFLoader,
    Docx2txtLoader,
    UnstructuredWordDocumentLoader
)
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
import chromadb
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
from app.core.config import envs
from app.core.logging import LogCategory, LogLayer, AppLoggerAdapter, extra_
from .base import BaseChunkCreationService


logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.AGENT,
        "component": __name__,
    },
)

class ChunkCreationService(BaseChunkCreationService):
    def __init__(self):
        logger.debug("Initializing ChunkCreationService")
        super().__init__()
        logger.info("ChunkCreationService initialized")

    def _load_kb_file(self, filepath):
        ext = Path(filepath).suffix.lower()
        logger.debug(f"Loading knowledge base file: {filepath}, extension: {ext}")

        try:
            if ext in [".md", ".txt"]:
                logger.debug(f"Loading {ext} file with TextLoader")
                docs = TextLoader(
                    file_path=filepath,
                    encoding="utf-8"
                ).load()
            elif ext == ".pdf":
                logger.debug("Loading PDF file with PyMuPDFLoader")
                docs = PyMuPDFLoader(filepath).load()
            elif ext == ".docx": 
                logger.debug("Loading DOCX file with Docx2txtLoader")
                docs = Docx2txtLoader(filepath).load()
            elif ext == ".doc":
                logger.debug("Loading DOC file with UnstructuredWordDocumentLoader")
                docs = UnstructuredWordDocumentLoader(filepath).load()
            else:
                logger.error(f"Unsupported file type: {ext}")
                raise ValueError(f"Unsupported file type: {ext}")
            
            logger.info(f"Loaded {len(docs)} document(s) from {filepath}")
            return docs
        except Exception as e:
            logger.exception(f"Error loading file {filepath}: {e}", exc_info=True)
            raise
        
    def create_chunks(self, filepath, chunk_size, overlapping):
        logger.info((
            f"Creating chunks from {filepath} - chunk_size: {chunk_size}, "
            f"overlap: {overlapping}"
        ))
        semantic_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlapping,
            separators=["\n\n", "\n", " ", ""]
        )
        
        raw_docs = self._load_kb_file(filepath)
        ext = Path(filepath).suffix.lower()
        
        raw_chunks = []
        for doc in raw_docs:
            base_metadata = {
                "source": filepath,
                "file_type": ext,
            }

            if ext == ".md":
                logger.debug("Processing markdown file with header splitter")
                markdown_header_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=[
                        ("#", "h1"),
                        ("##", "h2"),
                        # ("###", "h3"),
                    ],
                    strip_headers=False
                )
                header_docs = markdown_header_splitter.split_text(
                    doc.page_content
                )

                for hdoc in header_docs:
                    hdoc.metadata.update(base_metadata)

                    sub_chunks = semantic_splitter.split_documents([hdoc])
                    raw_chunks.extend(sub_chunks)

            else:
                logger.debug(f"Processing {ext} file with semantic splitter")
                doc.metadata.update(base_metadata)
                chunks = semantic_splitter.split_documents([doc])
                raw_chunks.extend(chunks)

        final_chunks = []
        for i, doc in enumerate(raw_chunks):
            chunk = {
                "_id": f"im-kb-{doc.metadata['source']}-chunk-{i+1}",
                "text": doc.page_content,
                **doc.metadata
            }
            final_chunks.append(chunk)
        
        logger.info(f"Created {len(final_chunks)} final chunks from {filepath}")
        return final_chunks


class ChromaVectorIndexService:
    def __init__(self):
        logger.debug("Initializing ChromaVectorIndexService")
        self.embedder = GoogleGenerativeAiEmbeddingFunction(
            api_key_env_var="GOOGLE_API_KEY",
            model_name=envs.EMBEDDING_MODEL,
        )
        logger.debug(f"Using embedding model: {envs.EMBEDDING_MODEL}")
        self.client = chromadb.PersistentClient()
        logger.debug(f"Creating/accessing ChromaDB collection: {envs.VECTOR_DB_NAME}")
        self.cm_index = self.client.create_collection(
            name=envs.VECTOR_DB_NAME,
            embedding_function=self.embedder,
            get_or_create=True
        )
        logger.info(
            f"""ChromaVectorIndexService initialized with collection: {
                envs.VECTOR_DB_NAME
            }"""
        )

    async def update_index(self, chunks:list, update_source:str):
        logger.info((
            f"Updating ChromaDB index with {len(chunks)} "
            f"chunks from source: {update_source}"
        ))
        try:
            current_count = self.cm_index.count()
            logger.debug(f"Current collection count: {current_count}")
            
            if current_count != 0:
                chunk_ids = [doc["_id"] for doc in chunks]
                logger.debug(
                    f"Deleting {len(chunk_ids)} existing chunks from collection"
                )
                self.cm_index.delete(ids=chunk_ids)
            
            logger.debug(f"Adding {len(chunks)} new chunks to collection")
            self.cm_index.add(
                documents=[doc.get("text") for doc in chunks],
                ids=[doc["_id"] for doc in chunks],
            )
            logger.info(
                f"Successfully updated ChromaDB index with {len(chunks)} chunks"
            )
        except Exception as e:
            logger.exception(f"Error updating ChromaDB index: {e}", exc_info=True)
            raise

    async def query_index(self, text_query: str, rerank: bool = False):
        logger.debug(
            f"""Querying ChromaDB - query: {
                text_query[:100] if len(text_query) > 100 else text_query
            }, top_k: {envs.NO_TOP_K_CHUNKS}"""
        )
        try:
            results = self.cm_index.query(
                query_texts=[text_query],
                n_results=envs.NO_TOP_K_CHUNKS
            )
            chunks = results["documents"][0]
            logger.debug(f"Retrieved {len(chunks)} chunks from ChromaDB")

            if not chunks:
                logger.warning(f"No chunks found for query: {text_query[:100]}")
                return "Not found any information for given query!"

            knowledge = "# Retrived Information"
            for i, chunk in enumerate(chunks, start=1):
                knowledge += f"\n## Chunk {i}\n{chunk}"
            
            logger.info(
                f"Successfully queried ChromaDB, returning {len(chunks)} chunks"
            )
            return knowledge
        except Exception as e:
            logger.exception(f"Error querying ChromaDB: {e}", exc_info=True)
            raise

    async def close(self):
        logger.debug("Closing ChromaVectorIndexService (no-op for persistent client)")
        pass