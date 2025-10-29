"""
Embedding Module - Text to Vector Conversion
Supports multiple embedding models
"""
from typing import List, Union
from sentence_transformers import SentenceTransformer
from loguru import logger

from config import settings


class EmbeddingModel:
    """
    Embedding model for converting text to vectors

    Uses sentence-transformers for efficient embedding generation
    Supports multilingual models for Chinese compliance documents
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding model

        Args:
            model_name: Model name (default from settings)
        """
        from typing import Optional

        self.model_name = model_name or settings.embedding_model

        logger.info(f"Loading embedding model: {self.model_name}")

        try:
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()

            logger.info(f"Embedding model loaded successfully (dimension: {self.dimension})")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text

        Args:
            text: Input text

        Returns:
            List of floats representing embedding vector
        """
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")

            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        from sentence_transformers import util

        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)

        similarity = util.cos_sim(emb1, emb2)

        return float(similarity[0][0])


# Global embedding model instance (lazy initialization)
_global_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    """
    Get global embedding model instance

    Returns:
        EmbeddingModel: Shared embedding model
    """
    global _global_embedding_model

    if _global_embedding_model is None:
        _global_embedding_model = EmbeddingModel()

    return _global_embedding_model
