"""
RAG Retriever Module - Knowledge Retrieval
Combines vector search with re-ranking for accurate retrieval
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

from .vector_store import MilvusVectorStore
from .embeddings import get_embedding_model
from config import settings


@dataclass
class RetrievedDocument:
    """Single retrieved document"""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class RAGRetriever:
    """
    Retrieval-Augmented Generation Retriever

    Provides semantic search over compliance documents
    """

    def __init__(
        self,
        vector_store: Optional[MilvusVectorStore] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ):
        """
        Initialize RAG retriever

        Args:
            vector_store: Vector store instance (creates new if None)
            top_k: Number of documents to retrieve (default from settings)
            similarity_threshold: Minimum similarity score (default from settings)
        """
        self.vector_store = vector_store or MilvusVectorStore()
        self.embedding_model = get_embedding_model()

        self.top_k = top_k or settings.top_k_documents
        self.similarity_threshold = similarity_threshold or settings.similarity_threshold

        logger.info("RAG Retriever initialized")

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for query

        Args:
            query: Search query
            top_k: Number of documents to retrieve (overrides default)
            filter_metadata: Optional metadata filters

        Returns:
            List of retrieved documents

        Raises:
            Exception: If retrieval fails
        """
        logger.info(f"Retrieving documents for query: {query[:100]}...")

        try:
            # Generate query embedding
            query_embedding = self.embedding_model.embed_text(query)

            # Build filter expression if needed
            filter_expr = None
            if filter_metadata:
                filter_expr = self._build_filter_expression(filter_metadata)

            # Search in vector store
            k = top_k or self.top_k
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=k,
                filter_expr=filter_expr
            )

            # Filter by similarity threshold and convert to RetrievedDocument
            documents = []
            for result in results:
                if result["score"] >= self.similarity_threshold:
                    documents.append(RetrievedDocument(
                        doc_id=result["doc_id"],
                        content=result["content"],
                        score=result["score"],
                        metadata=result["metadata"]
                    ))

            logger.info(f"Retrieved {len(documents)} documents above threshold")

            return documents

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise

    def retrieve_with_context(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[RetrievedDocument]:
        """
        Retrieve documents with conversation context

        Enhances query with conversation history for better retrieval

        Args:
            query: Current query
            conversation_history: Previous conversation context
            top_k: Number of documents to retrieve

        Returns:
            List of retrieved documents
        """
        # Enhance query with context
        enhanced_query = query
        if conversation_history:
            enhanced_query = f"Context: {conversation_history}\n\nQuery: {query}"

        return self.retrieve(enhanced_query, top_k=top_k)

    def format_context(
        self,
        documents: List[RetrievedDocument],
        max_length: int = 2000
    ) -> str:
        """
        Format retrieved documents as context for LLM

        Args:
            documents: Retrieved documents
            max_length: Maximum character length

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant documents found."

        context_parts = []
        current_length = 0

        for i, doc in enumerate(documents, 1):
            # Format document
            doc_text = f"[Document {i}] (Score: {doc.score:.2f})\n{doc.content}\n"

            # Check if adding this document would exceed max_length
            if current_length + len(doc_text) > max_length:
                break

            context_parts.append(doc_text)
            current_length += len(doc_text)

        context = "\n".join(context_parts)

        logger.info(f"Formatted context from {len(context_parts)} documents ({current_length} chars)")

        return context

    def _build_filter_expression(self, metadata: Dict[str, Any]) -> str:
        """
        Build Milvus filter expression from metadata

        Args:
            metadata: Filter criteria

        Returns:
            Filter expression string
        """
        # Simple implementation - can be extended for complex filters
        conditions = []

        for key, value in metadata.items():
            if isinstance(value, str):
                conditions.append(f'metadata["{key}"] == "{value}"')
            elif isinstance(value, (int, float)):
                conditions.append(f'metadata["{key}"] == {value}')
            elif isinstance(value, list):
                # IN clause
                values = ", ".join([f'"{v}"' if isinstance(v, str) else str(v) for v in value])
                conditions.append(f'metadata["{key}"] in [{values}]')

        return " and ".join(conditions) if conditions else None


class DocumentProcessor:
    """
    Processes and indexes documents into vector store

    Handles document chunking and embedding generation
    """

    def __init__(
        self,
        vector_store: MilvusVectorStore,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initialize document processor

        Args:
            vector_store: Vector store for indexing
            chunk_size: Maximum chunk size (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
        """
        self.vector_store = vector_store
        self.embedding_model = get_embedding_model()

        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        logger.info(f"Document processor initialized (chunk_size={self.chunk_size})")

    def process_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Process and index a single document

        Args:
            doc_id: Document identifier
            content: Document content
            metadata: Optional metadata

        Returns:
            Number of chunks indexed
        """
        logger.info(f"Processing document: {doc_id}")

        # Chunk document
        chunks = self._chunk_text(content)

        # Generate embeddings
        embeddings = self.embedding_model.embed_batch(chunks)

        # Prepare data
        doc_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadata_list = [
            {
                **(metadata or {}),
                "source_doc_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]

        # Insert into vector store
        self.vector_store.insert_documents(
            doc_ids=doc_ids,
            contents=chunks,
            embeddings=embeddings,
            metadata_list=metadata_list
        )

        logger.info(f"Indexed {len(chunks)} chunks for document {doc_id}")

        return len(chunks)

    def process_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Process multiple documents

        Args:
            documents: List of documents, each with 'doc_id', 'content', and optional 'metadata'

        Returns:
            Total number of chunks indexed
        """
        total_chunks = 0

        for doc in documents:
            chunks = self.process_document(
                doc_id=doc["doc_id"],
                content=doc["content"],
                metadata=doc.get("metadata")
            )
            total_chunks += chunks

        logger.info(f"Batch processing complete: {total_chunks} total chunks indexed")

        return total_chunks

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Simple character-based chunking
        # Can be enhanced with semantic chunking or sentence-based splitting

        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for delimiter in ['。', '！', '？', '.', '!', '?', '\n\n']:
                    last_delim = chunk.rfind(delimiter)
                    if last_delim > self.chunk_size * 0.5:  # At least 50% of chunk size
                        chunk = chunk[:last_delim + 1]
                        end = start + last_delim + 1
                        break

            chunks.append(chunk.strip())

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks
