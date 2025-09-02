"""LlamaIndex development environment service for document processing and retrieval."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class LlamaIndexService:
    """Service for managing LlamaIndex document processing and retrieval."""
    
    def __init__(self) -> None:
        """Initialize the LlamaIndex service."""
        self.settings = get_settings()
        self._llm: Optional[Ollama] = None
        self._embedding_model: Optional[OllamaEmbedding] = None
        self._index: Optional[VectorStoreIndex] = None
        self._query_engine = None
        self._debug_handler: Optional[LlamaDebugHandler] = None
        
        self._setup_llamaindex()
    
    def _setup_llamaindex(self) -> None:
        """Setup LlamaIndex with proper configuration and observability."""
        try:
            # Initialize LLM
            self._llm = Ollama(
                model=self.settings.ollama.llamaindex_llm_model,
                base_url=self.settings.ollama.base_url,
                request_timeout=self.settings.ollama.request_timeout,
            )
            
            # Initialize embedding model (using same model for simplicity)
            self._embedding_model = OllamaEmbedding(
                model_name=self.settings.ollama.llamaindex_llm_model,
                base_url=self.settings.ollama.base_url,
            )
            
            # Setup observability if enabled
            if self.settings.llamaindex.enable_observability:
                self._debug_handler = LlamaDebugHandler(print_trace_on_end=True)
                callback_manager = CallbackManager([self._debug_handler])
                Settings.callback_manager = callback_manager
            
            # Configure global settings
            Settings.llm = self._llm
            Settings.embed_model = self._embedding_model
            Settings.node_parser = SentenceSplitter(
                chunk_size=self.settings.llamaindex.chunk_size,
                chunk_overlap=self.settings.llamaindex.chunk_overlap,
            )
            
            logger.info("LlamaIndex service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LlamaIndex service: {e}")
            raise
    
    async def load_documents(self, directory_path: Optional[Path] = None) -> List[str]:
        """
        Load documents from the specified directory.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of loaded document IDs
        """
        try:
            if directory_path is None:
                directory_path = self.settings.llamaindex.data_path
            
            if not directory_path.exists():
                logger.warning(f"Directory {directory_path} does not exist")
                return []
            
            # Load documents
            reader = SimpleDirectoryReader(
                input_dir=str(directory_path),
                recursive=True,
                required_exts=[".txt", ".md", ".pdf", ".docx"],
            )
            
            documents = reader.load_data()
            
            if not documents:
                logger.warning(f"No documents found in {directory_path}")
                return []
            
            logger.info(f"Loaded {len(documents)} documents from {directory_path}")
            return [doc.doc_id for doc in documents]
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            raise
    
    async def create_index(self, documents_path: Optional[Path] = None) -> bool:
        """
        Create or update the vector store index.
        
        Args:
            documents_path: Path to documents directory
            
        Returns:
            True if index created successfully, False otherwise
        """
        try:
            if documents_path is None:
                documents_path = self.settings.llamaindex.data_path
            
            # Load documents
            document_ids = await self.load_documents(documents_path)
            if not document_ids:
                logger.warning("No documents to index")
                return False
            
            # Create reader and load documents
            reader = SimpleDirectoryReader(
                input_dir=str(documents_path),
                recursive=True,
                required_exts=[".txt", ".md", ".pdf", ".docx"],
            )
            documents = reader.load_data()
            
            # Create index
            self._index = VectorStoreIndex.from_documents(documents)
            
            # Save index to storage
            storage_path = self.settings.llamaindex.data_path / "storage"
            storage_path.mkdir(exist_ok=True)
            self._index.storage_context.persist(persist_dir=str(storage_path))
            
            # Create query engine
            self._query_engine = self._index.as_query_engine()
            
            logger.info(f"Index created with {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    async def load_index(self) -> bool:
        """
        Load existing index from storage.
        
        Returns:
            True if index loaded successfully, False otherwise
        """
        try:
            storage_path = self.settings.llamaindex.data_path / "storage"
            
            if not storage_path.exists():
                logger.info("No existing index found, creating new one")
                return await self.create_index()
            
            # Load index from storage
            storage_context = StorageContext.from_defaults(persist_dir=str(storage_path))
            self._index = load_index_from_storage(storage_context)
            
            # Create query engine
            self._query_engine = self._index.as_query_engine()
            
            logger.info("Index loaded successfully from storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    async def query(self, query_text: str) -> Dict[str, Any]:
        """
        Query the index with the given text.
        
        Args:
            query_text: Query string
            
        Returns:
            Query result with response and metadata
        """
        try:
            if not self._query_engine:
                # Try to load existing index
                if not await self.load_index():
                    raise ValueError("No index available for querying")
            
            # Execute query
            response = self._query_engine.query(query_text)
            
            # Extract metadata
            metadata = {
                "source_nodes": [
                    {
                        "node_id": node.node_id,
                        "score": node.score,
                        "text_snippet": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                    }
                    for node in response.source_nodes
                ],
                "query": query_text,
                "response_time": getattr(response, "response_time", None),
            }
            
            return {
                "response": str(response),
                "metadata": metadata,
            }
            
        except Exception as e:
            logger.error(f"Failed to query index: {e}")
            raise
    
    async def add_document(self, document_text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a single document to the index.
        
        Args:
            document_text: Document content
            document_id: Unique document identifier
            metadata: Optional metadata for the document
            
        Returns:
            True if document added successfully, False otherwise
        """
        try:
            from llama_index.core import Document
            
            # Create document
            doc = Document(
                text=document_text,
                doc_id=document_id,
                metadata=metadata or {}
            )
            
            if self._index is None:
                # Create new index with this document
                self._index = VectorStoreIndex.from_documents([doc])
            else:
                # Add document to existing index
                self._index.insert(doc)
            
            # Update query engine
            self._query_engine = self._index.as_query_engine()
            
            # Save updated index
            storage_path = self.settings.llamaindex.data_path / "storage"
            storage_path.mkdir(exist_ok=True)
            self._index.storage_context.persist(persist_dir=str(storage_path))
            
            logger.info(f"Document {document_id} added to index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    async def get_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information from LlamaIndex.
        
        Returns:
            Debug information dictionary
        """
        debug_info = {
            "llm_model": self.settings.ollama.llamaindex_llm_model,
            "ollama_base_url": self.settings.ollama.base_url,
            "index_available": self._index is not None,
            "query_engine_available": self._query_engine is not None,
            "chunk_size": self.settings.llamaindex.chunk_size,
            "chunk_overlap": self.settings.llamaindex.chunk_overlap,
        }
        
        if self._debug_handler:
            debug_info["event_pairs"] = self._debug_handler.get_event_pairs()
        
        return debug_info
    
    async def health_check(self) -> Dict[str, str]:
        """
        Perform health check on LlamaIndex service.
        
        Returns:
            Health status dictionary
        """
        try:
            # Test LLM connection
            if self._llm:
                test_response = await self._llm.acomplete("Hello")
                llm_status = "healthy" if test_response else "error"
            else:
                llm_status = "not_initialized"
            
            # Check index status
            index_status = "available" if self._index else "not_loaded"
            
            # Check storage
            storage_path = self.settings.llamaindex.data_path / "storage"
            storage_status = "available" if storage_path.exists() else "not_found"
            
            return {
                "llm": llm_status,
                "index": index_status,
                "storage": storage_status,
                "overall": "healthy" if llm_status == "healthy" else "degraded"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "llm": "error",
                "index": "error", 
                "storage": "error",
                "overall": "unhealthy",
                "error": str(e)
            }


# Global service instance
_llamaindex_service: Optional[LlamaIndexService] = None


async def get_llamaindex_service() -> LlamaIndexService:
    """Get the global LlamaIndex service instance."""
    global _llamaindex_service
    if _llamaindex_service is None:
        _llamaindex_service = LlamaIndexService()
    return _llamaindex_service