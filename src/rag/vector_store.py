"""
Vector Store Module - Milvus Integration
Handles vector database operations for document storage and retrieval
"""
from typing import List, Dict, Any, Optional, Tuple
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)
from loguru import logger

from config import settings


class MilvusVectorStore:
    """
    Milvus vector store for document embeddings

    Provides:
    - Collection management
    - Document insertion
    - Similarity search
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None
    ):
        """
        Initialize Milvus vector store

        Args:
            collection_name: Name of collection (default from settings)
            dimension: Vector dimension (default from settings)
        """
        self.collection_name = collection_name or settings.milvus_collection_name
        self.dimension = dimension or settings.embedding_dimension

        self.collection: Optional[Collection] = None
        self.is_connected = False

        logger.info(f"Initialized MilvusVectorStore for collection '{self.collection_name}'")

    def connect(self):
        """
        Connect to Milvus server

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info(f"Connecting to Milvus at {settings.milvus_host}:{settings.milvus_port}")

            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port,
                user=settings.milvus_user or "",
                password=settings.milvus_password or ""
            )

            self.is_connected = True
            logger.info("Successfully connected to Milvus")

            # Load or create collection
            self._load_or_create_collection()

        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            raise

    def disconnect(self):
        """Disconnect from Milvus"""
        if self.is_connected:
            connections.disconnect("default")
            self.is_connected = False
            logger.info("Disconnected from Milvus")

    def _load_or_create_collection(self):
        """Load existing collection or create new one"""
        if utility.has_collection(self.collection_name):
            logger.info(f"Loading existing collection: {self.collection_name}")
            self.collection = Collection(self.collection_name)
            self.collection.load()
        else:
            logger.info(f"Creating new collection: {self.collection_name}")
            self._create_collection()

    def _create_collection(self):
        """
        Create new Milvus collection with schema

        Schema:
        - id: Primary key (auto-generated)
        - doc_id: Document identifier
        - content: Document text content
        - embedding: Vector embedding
        - metadata: JSON metadata
        """
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]

        schema = CollectionSchema(
            fields=fields,
            description="Compliance documents collection"
        )

        # Create collection
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )

        # Create index for vector field
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }

        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        self.collection.load()

        logger.info(f"Created collection '{self.collection_name}' with dimension {self.dimension}")

    def insert_documents(
        self,
        doc_ids: List[str],
        contents: List[str],
        embeddings: List[List[float]],
        metadata_list: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Insert documents into collection

        Args:
            doc_ids: List of document IDs
            contents: List of document contents
            embeddings: List of embedding vectors
            metadata_list: List of metadata dictionaries

        Returns:
            List of inserted IDs

        Raises:
            Exception: If insertion fails
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to Milvus. Call connect() first.")

        if not (len(doc_ids) == len(contents) == len(embeddings) == len(metadata_list)):
            raise ValueError("All input lists must have the same length")

        try:
            # Prepare data
            data = [
                doc_ids,
                contents,
                embeddings,
                metadata_list
            ]

            # Insert
            result = self.collection.insert(data)

            # Flush to ensure data is persisted
            self.collection.flush()

            logger.info(f"Inserted {len(doc_ids)} documents into collection")

            return result.primary_keys

        except Exception as e:
            logger.error(f"Failed to insert documents: {str(e)}")
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_expr: Optional filter expression

        Returns:
            List of search results with content and metadata

        Raises:
            Exception: If search fails
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to Milvus. Call connect() first.")

        try:
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }

            # Define output fields
            output_fields = ["doc_id", "content", "metadata"]

            # Execute search
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=output_fields
            )

            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "doc_id": hit.entity.get("doc_id"),
                        "content": hit.entity.get("content"),
                        "metadata": hit.entity.get("metadata"),
                        "distance": hit.distance,
                        "score": 1.0 / (1.0 + hit.distance)  # Convert distance to similarity score
                    })

            logger.info(f"Search returned {len(formatted_results)} results")

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    def delete_by_doc_id(self, doc_id: str):
        """
        Delete documents by document ID

        Args:
            doc_id: Document ID to delete
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to Milvus. Call connect() first.")

        try:
            expr = f'doc_id == "{doc_id}"'
            self.collection.delete(expr)
            logger.info(f"Deleted documents with doc_id: {doc_id}")

        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Dict with collection stats
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to Milvus. Call connect() first.")

        stats = self.collection.num_entities

        return {
            "collection_name": self.collection_name,
            "total_documents": stats,
            "dimension": self.dimension
        }

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
