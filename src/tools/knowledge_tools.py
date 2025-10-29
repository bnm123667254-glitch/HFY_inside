"""
Knowledge Tools - RAG-based Tools
Provides knowledge search and document summarization
"""
from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from .base import BaseTool, ToolOutput
from ..rag import RAGRetriever, RetrievedDocument


class KnowledgeSearchTool(BaseTool):
    """
    Tool for searching compliance knowledge base

    Uses RAG retrieval to find relevant documents
    """

    def __init__(
        self,
        retriever: RAGRetriever,
        name: str = "knowledge_search",
        description: str = "Search compliance documents for relevant information"
    ):
        """
        Initialize knowledge search tool

        Args:
            retriever: RAG retriever instance
            name: Tool name
            description: Tool description
        """
        super().__init__(name, description)
        self.retriever = retriever

    def invoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Search knowledge base

        Args:
            input_data: Must contain 'query' key

        Returns:
            ToolOutput with retrieved documents
        """
        try:
            query = input_data.get("query")
            if not query:
                return ToolOutput(
                    success=False,
                    data=None,
                    error="Missing 'query' parameter"
                )

            top_k = input_data.get("top_k", 5)
            filter_metadata = input_data.get("filter_metadata")

            logger.info(f"Searching knowledge base: {query[:100]}")

            # Retrieve documents
            documents = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata
            )

            # Format results
            results = [
                {
                    "doc_id": doc.doc_id,
                    "content": doc.content,
                    "score": doc.score,
                    "metadata": doc.metadata
                }
                for doc in documents
            ]

            return ToolOutput(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "count": len(results)
                },
                metadata={
                    "tool": self.name,
                    "top_k": top_k
                }
            )

        except Exception as e:
            logger.error(f"Knowledge search failed: {str(e)}")
            return ToolOutput(
                success=False,
                data=None,
                error=str(e)
            )


class DocumentSummarizeTool(BaseTool):
    """
    Tool for summarizing compliance documents

    Uses LLM to generate concise summaries
    """

    SUMMARIZE_PROMPT = """You are a compliance expert. Summarize the following compliance documents concisely.

Focus on:
1. Key compliance requirements
2. Important regulations and rules
3. Actionable items or recommendations

Documents:
{documents}

Query context: {query}

Generate a comprehensive yet concise summary in Chinese. Highlight the most important points.
"""

    def __init__(
        self,
        llm: BaseChatModel,
        name: str = "document_summarize",
        description: str = "Summarize compliance documents or search results"
    ):
        """
        Initialize document summarize tool

        Args:
            llm: Language model for summarization
            name: Tool name
            description: Tool description
        """
        super().__init__(name, description)
        self.llm = llm

        # Create prompt template
        self.prompt = ChatPromptTemplate.from_template(self.SUMMARIZE_PROMPT)

    def invoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Summarize documents

        Args:
            input_data: Must contain 'documents' (list or string) and optionally 'query'

        Returns:
            ToolOutput with summary
        """
        try:
            documents = input_data.get("documents")
            query = input_data.get("query", "")

            if not documents:
                # Check if documents from previous step
                step_output = input_data.get("context", {})
                for key, value in step_output.items():
                    if key.endswith("_output") and isinstance(value, dict):
                        documents = value.get("data", {}).get("results")
                        if documents:
                            break

            if not documents:
                return ToolOutput(
                    success=False,
                    data=None,
                    error="Missing 'documents' parameter"
                )

            # Format documents
            if isinstance(documents, list):
                doc_text = "\n\n".join([
                    f"[Document {i+1}]\n{doc.get('content', str(doc))}"
                    for i, doc in enumerate(documents)
                ])
            else:
                doc_text = str(documents)

            logger.info("Generating document summary")

            # Generate summary
            messages = self.prompt.format_messages(
                documents=doc_text[:4000],  # Limit to avoid token overflow
                query=query
            )

            response = self.llm.invoke(messages)
            summary = response.content

            return ToolOutput(
                success=True,
                data={
                    "summary": summary,
                    "query": query,
                    "document_count": len(documents) if isinstance(documents, list) else 1
                },
                metadata={
                    "tool": self.name
                }
            )

        except Exception as e:
            logger.error(f"Document summarization failed: {str(e)}")
            return ToolOutput(
                success=False,
                data=None,
                error=str(e)
            )


class ComplianceCheckTool(BaseTool):
    """
    Tool for checking compliance requirements

    Analyzes scenarios against compliance rules
    """

    COMPLIANCE_CHECK_PROMPT = """You are a compliance expert. Analyze the following scenario against relevant compliance requirements.

Scenario:
{scenario}

Relevant Compliance Documents:
{documents}

Provide a detailed compliance analysis including:
1. Applicable regulations
2. Compliance requirements that apply
3. Potential compliance risks
4. Recommendations for ensuring compliance

Answer in Chinese with clear, actionable guidance.
"""

    def __init__(
        self,
        llm: BaseChatModel,
        retriever: RAGRetriever,
        name: str = "compliance_check",
        description: str = "Check compliance requirements for specific scenarios"
    ):
        """
        Initialize compliance check tool

        Args:
            llm: Language model
            retriever: RAG retriever
            name: Tool name
            description: Tool description
        """
        super().__init__(name, description)
        self.llm = llm
        self.retriever = retriever

        self.prompt = ChatPromptTemplate.from_template(self.COMPLIANCE_CHECK_PROMPT)

    def invoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Check compliance for scenario

        Args:
            input_data: Must contain 'scenario'

        Returns:
            ToolOutput with compliance analysis
        """
        try:
            scenario = input_data.get("scenario")
            if not scenario:
                return ToolOutput(
                    success=False,
                    data=None,
                    error="Missing 'scenario' parameter"
                )

            logger.info("Performing compliance check")

            # Retrieve relevant documents
            documents = self.retriever.retrieve(query=scenario, top_k=5)

            # Format documents
            doc_text = "\n\n".join([
                f"[Document {i+1}] (Score: {doc.score:.2f})\n{doc.content}"
                for i, doc in enumerate(documents)
            ])

            # Generate compliance analysis
            messages = self.prompt.format_messages(
                scenario=scenario,
                documents=doc_text[:3000]
            )

            response = self.llm.invoke(messages)
            analysis = response.content

            return ToolOutput(
                success=True,
                data={
                    "scenario": scenario,
                    "analysis": analysis,
                    "referenced_documents": len(documents)
                },
                metadata={
                    "tool": self.name
                }
            )

        except Exception as e:
            logger.error(f"Compliance check failed: {str(e)}")
            return ToolOutput(
                success=False,
                data=None,
                error=str(e)
            )
