"""
API Dependencies - Dependency Injection for FastAPI
"""
from functools import lru_cache
from loguru import logger

from ..models import get_llm
from ..agent import ComplianceAgent
from ..rag import RAGRetriever, MilvusVectorStore, DocumentProcessor
from ..tools.factory import ToolFactory
from ..agent.memory import ConversationMemory
from config import settings


# Global instances (initialized once)
_vector_store: MilvusVectorStore = None
_retriever: RAGRetriever = None
_agent: ComplianceAgent = None
_document_processor: DocumentProcessor = None


def init_components():
    """
    Initialize all system components

    Should be called during application startup
    """
    global _vector_store, _retriever, _agent, _document_processor

    logger.info("Initializing system components")

    # Initialize vector store
    _vector_store = MilvusVectorStore()
    _vector_store.connect()

    # Initialize retriever
    _retriever = RAGRetriever(_vector_store)

    # Initialize LLM
    llm = get_llm(temperature=0.7)

    # Create tools
    tools = ToolFactory.create_all_tools(llm, _retriever)

    # Initialize agent
    _agent = ComplianceAgent(llm, tools=tools, enable_review=True)

    # Initialize document processor
    _document_processor = DocumentProcessor(_vector_store)

    logger.info("System components initialized successfully")


def shutdown_components():
    """
    Cleanup components during shutdown
    """
    global _vector_store

    logger.info("Shutting down system components")

    if _vector_store:
        _vector_store.disconnect()

    logger.info("System components shut down")


def get_vector_store() -> MilvusVectorStore:
    """Get vector store instance"""
    if _vector_store is None:
        raise RuntimeError("Components not initialized. Call init_components() first.")
    return _vector_store


def get_retriever() -> RAGRetriever:
    """Get retriever instance"""
    if _retriever is None:
        raise RuntimeError("Components not initialized. Call init_components() first.")
    return _retriever


def get_agent() -> ComplianceAgent:
    """Get agent instance"""
    if _agent is None:
        raise RuntimeError("Components not initialized. Call init_components() first.")
    return _agent


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance"""
    if _document_processor is None:
        raise RuntimeError("Components not initialized. Call init_components() first.")
    return _document_processor


@lru_cache()
def get_memory_manager() -> dict:
    """Get memory manager (simple dict cache for sessions)"""
    return {}
