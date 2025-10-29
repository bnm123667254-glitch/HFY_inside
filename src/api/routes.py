"""
API Routes - FastAPI Endpoints
"""
import time
from typing import Dict
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
import uuid

from .schemas import (
    QueryRequest, QueryResponse,
    AgentTaskRequest, AgentTaskResponse, TaskStepResponse,
    DocumentUploadRequest, DocumentUploadResponse,
    BatchDocumentUploadRequest, BatchDocumentUploadResponse,
    ChatRequest, ChatResponse,
    HealthResponse, StatsResponse,
    RetrievedDocumentResponse
)
from ..agent import ComplianceAgent
from ..rag import RAGRetriever, DocumentProcessor
from ..agent.memory import ConversationMemory
from .dependencies import get_agent, get_retriever, get_document_processor, get_memory_manager


# Create router
router = APIRouter()


# Health and Info Endpoints
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        components={
            "agent": "operational",
            "rag": "operational",
            "vector_store": "operational"
        }
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    retriever: RAGRetriever = Depends(get_retriever)
):
    """Get system statistics"""
    try:
        vector_stats = retriever.vector_store.get_collection_stats()

        return StatsResponse(
            vector_store=vector_stats,
            tools=["knowledge_search", "document_summarize", "compliance_check",
                   "email_draft", "report_generate", "summary_enhance"],
            uptime=time.time()  # Simplified, should track actual uptime
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Query Endpoints
@router.post("/query", response_model=QueryResponse)
async def query_knowledge(
    request: QueryRequest,
    retriever: RAGRetriever = Depends(get_retriever),
    agent: ComplianceAgent = Depends(get_agent)
):
    """
    Simple Q&A query endpoint

    Retrieves relevant documents and generates answer
    """
    try:
        logger.info(f"Processing query: {request.query}")

        # Retrieve documents
        documents = retriever.retrieve(
            query=request.query,
            top_k=request.top_k
        )

        if not documents:
            return QueryResponse(
                query=request.query,
                answer="未找到相关的合规文档。",
                retrieved_documents=[],
                metadata={"document_count": 0}
            )

        # Format context
        context = retriever.format_context(documents)

        # Generate answer using agent (simplified single-step)
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_template(
            """Based on the following compliance documents, answer the user's question.

Documents:
{context}

Question: {question}

Provide a clear, accurate answer in Chinese. Cite specific documents when relevant.

Answer:"""
        )

        messages = prompt.format_messages(
            context=context,
            question=request.query
        )

        response = agent.llm.invoke(messages)
        answer = response.content

        # Prepare response
        retrieved_docs = None
        if request.include_context:
            retrieved_docs = [
                RetrievedDocumentResponse(
                    doc_id=doc.doc_id,
                    content=doc.content,
                    score=doc.score,
                    metadata=doc.metadata
                )
                for doc in documents
            ]

        return QueryResponse(
            query=request.query,
            answer=answer,
            retrieved_documents=retrieved_docs,
            metadata={
                "document_count": len(documents),
                "top_score": documents[0].score if documents else 0
            }
        )

    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent Task Endpoints
@router.post("/agent/task", response_model=AgentTaskResponse)
async def execute_agent_task(
    request: AgentTaskRequest,
    agent: ComplianceAgent = Depends(get_agent)
):
    """
    Execute complex agent task

    Uses P-E-R framework for multi-step execution
    """
    try:
        logger.info(f"Executing agent task: {request.task}")

        start_time = time.time()

        # Execute task
        result = await agent.run(
            task=request.task,
            context=request.context,
            parameters=request.parameters
        )

        execution_time = time.time() - start_time

        # Format steps
        steps = [
            TaskStepResponse(
                step_id=step_id,
                description=result.plan.steps[step_id - 1].description
                if step_id <= len(result.plan.steps) else "Unknown",
                tool=result.plan.steps[step_id - 1].tool
                if step_id <= len(result.plan.steps) else "Unknown",
                status=step_result.status.value,
                output=step_result.output,
                error=step_result.error,
                execution_time=step_result.execution_time
            )
            for step_id, step_result in result.execution_context.results.items()
        ]

        # Format review
        review_data = None
        if request.enable_review and result.review:
            review_data = {
                "passed": result.review.passed,
                "quality_score": result.review.quality_score,
                "completeness_score": result.review.completeness_score,
                "issues": result.review.issues,
                "recommendations": result.review.recommendations,
                "summary": result.review.summary
            }

        return AgentTaskResponse(
            task=request.task,
            success=result.success,
            final_output=result.final_output,
            steps=steps,
            review=review_data,
            report=result.report if request.enable_review else None,
            execution_time=execution_time,
            metadata={
                "total_steps": len(steps),
                "plan_complexity": result.plan.estimated_complexity
            }
        )

    except Exception as e:
        logger.error(f"Agent task execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Document Management Endpoints
@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: DocumentUploadRequest,
    processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Upload and index a single document
    """
    try:
        logger.info(f"Uploading document: {request.doc_id}")

        chunks_indexed = processor.process_document(
            doc_id=request.doc_id,
            content=request.content,
            metadata=request.metadata
        )

        return DocumentUploadResponse(
            doc_id=request.doc_id,
            chunks_indexed=chunks_indexed,
            success=True,
            message=f"Successfully indexed {chunks_indexed} chunks"
        )

    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        return DocumentUploadResponse(
            doc_id=request.doc_id,
            chunks_indexed=0,
            success=False,
            message=str(e)
        )


@router.post("/documents/upload/batch", response_model=BatchDocumentUploadResponse)
async def upload_documents_batch(
    request: BatchDocumentUploadRequest,
    processor: DocumentProcessor = Depends(get_document_processor)
):
    """
    Upload and index multiple documents
    """
    try:
        logger.info(f"Batch uploading {len(request.documents)} documents")

        details = []
        total_chunks = 0
        successful = 0
        failed = 0

        for doc_req in request.documents:
            try:
                chunks = processor.process_document(
                    doc_id=doc_req.doc_id,
                    content=doc_req.content,
                    metadata=doc_req.metadata
                )

                details.append(DocumentUploadResponse(
                    doc_id=doc_req.doc_id,
                    chunks_indexed=chunks,
                    success=True,
                    message=f"Successfully indexed {chunks} chunks"
                ))

                total_chunks += chunks
                successful += 1

            except Exception as e:
                logger.error(f"Failed to upload document {doc_req.doc_id}: {str(e)}")

                details.append(DocumentUploadResponse(
                    doc_id=doc_req.doc_id,
                    chunks_indexed=0,
                    success=False,
                    message=str(e)
                ))

                failed += 1

        return BatchDocumentUploadResponse(
            total_documents=len(request.documents),
            successful=successful,
            failed=failed,
            total_chunks=total_chunks,
            details=details
        )

    except Exception as e:
        logger.error(f"Batch upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat Endpoints
_memory_sessions: Dict[str, ConversationMemory] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: ComplianceAgent = Depends(get_agent),
    retriever: RAGRetriever = Depends(get_retriever)
):
    """
    Interactive chat endpoint with memory

    Maintains conversation context across sessions
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())

        if request.use_memory:
            if session_id not in _memory_sessions:
                _memory_sessions[session_id] = ConversationMemory()
            memory = _memory_sessions[session_id]
        else:
            memory = None

        logger.info(f"Processing chat message (session: {session_id})")

        # Get conversation context
        context = None
        if memory:
            context = memory.get_conversation_history()

        # Retrieve relevant documents
        documents = retriever.retrieve_with_context(
            query=request.message,
            conversation_history=context,
            top_k=3
        )

        # Format context
        doc_context = retriever.format_context(documents, max_length=1500)

        # Generate response
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_template(
            """You are a helpful compliance assistant. Answer the user's question based on the provided documents and conversation history.

Conversation History:
{history}

Relevant Documents:
{documents}

User: {message}