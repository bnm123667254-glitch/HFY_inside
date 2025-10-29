"""
Tool Factory - Convenient Tool Initialization
Creates and configures all tools with dependencies
"""
from typing import Dict, Any
from langchain_core.language_models import BaseChatModel
from loguru import logger

from .base import BaseTool
from .knowledge_tools import KnowledgeSearchTool, DocumentSummarizeTool, ComplianceCheckTool
from .generation_tools import EmailDraftTool, ReportGenerateTool, SummaryEnhanceTool
from ..rag import RAGRetriever, MilvusVectorStore


class ToolFactory:
    """
    Factory for creating and configuring tools

    Manages tool dependencies and initialization
    """

    @staticmethod
    def create_all_tools(
        llm: BaseChatModel,
        retriever: RAGRetriever
    ) -> Dict[str, BaseTool]:
        """
        Create all available tools

        Args:
            llm: Language model for tools that need it
            retriever: RAG retriever for knowledge tools

        Returns:
            Dict mapping tool names to tool instances
        """
        logger.info("Creating all tools")

        tools = {
            # Knowledge tools
            "knowledge_search": KnowledgeSearchTool(retriever),
            "document_summarize": DocumentSummarizeTool(llm),
            "compliance_check": ComplianceCheckTool(llm, retriever),

            # Generation tools
            "email_draft": EmailDraftTool(llm),
            "report_generate": ReportGenerateTool(llm),
            "summary_enhance": SummaryEnhanceTool(llm),
        }

        logger.info(f"Created {len(tools)} tools")

        return tools

    @staticmethod
    def create_knowledge_tools(
        llm: BaseChatModel,
        retriever: RAGRetriever
    ) -> Dict[str, BaseTool]:
        """
        Create only knowledge-related tools

        Args:
            llm: Language model
            retriever: RAG retriever

        Returns:
            Dict of knowledge tools
        """
        return {
            "knowledge_search": KnowledgeSearchTool(retriever),
            "document_summarize": DocumentSummarizeTool(llm),
            "compliance_check": ComplianceCheckTool(llm, retriever),
        }

    @staticmethod
    def create_generation_tools(llm: BaseChatModel) -> Dict[str, BaseTool]:
        """
        Create only generation tools

        Args:
            llm: Language model

        Returns:
            Dict of generation tools
        """
        return {
            "email_draft": EmailDraftTool(llm),
            "report_generate": ReportGenerateTool(llm),
            "summary_enhance": SummaryEnhanceTool(llm),
        }

    @staticmethod
    def create_tool_by_name(
        name: str,
        llm: BaseChatModel,
        retriever: RAGRetriever = None
    ) -> BaseTool:
        """
        Create specific tool by name

        Args:
            name: Tool name
            llm: Language model
            retriever: RAG retriever (optional, needed for some tools)

        Returns:
            Tool instance

        Raises:
            ValueError: If tool name not recognized
        """
        tool_map = {
            "knowledge_search": lambda: KnowledgeSearchTool(retriever),
            "document_summarize": lambda: DocumentSummarizeTool(llm),
            "compliance_check": lambda: ComplianceCheckTool(llm, retriever),
            "email_draft": lambda: EmailDraftTool(llm),
            "report_generate": lambda: ReportGenerateTool(llm),
            "summary_enhance": lambda: SummaryEnhanceTool(llm),
        }

        if name not in tool_map:
            raise ValueError(f"Unknown tool name: {name}")

        return tool_map[name]()
