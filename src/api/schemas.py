"""
API Schemas - Request and Response Models
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# Request Models
class QueryRequest(BaseModel):
    """Request for simple Q&A query"""
    query: str = Field(..., description="User's question or query")
    top_k: Optional[int] = Field(5, description="Number of documents to retrieve")
    include_context: bool = Field(True, description="Include retrieved context in response")


class AgentTaskRequest(BaseModel):
    """Request for agent task execution"""
    task: str = Field(..., description="Task description for agent")
    context: Optional[str] = Field(None, description="Optional conversation context")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")
    enable_review: bool = Field(True, description="Enable execution review")


class DocumentUploadRequest(BaseModel):
    """Request for uploading and indexing documents"""
    doc_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Document metadata")


class BatchDocumentUploadRequest(BaseModel):
    """Request for batch document upload"""
    documents: List[DocumentUploadRequest] = Field(..., description="List of documents to upload")


class ChatRequest(BaseModel):
    """Request for chat conversation"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    use_memory: bool = Field(True, description="Use conversation memory")


# Response Models
class RetrievedDocumentResponse(BaseModel):
    """Single retrieved document"""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    """Response for query request"""
    query: str
    answer: str
    retrieved_documents: Optional[List[RetrievedDocumentResponse]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskStepResponse(BaseModel):
    """Single task execution step"""
    step_id: int
    description: str
    tool: str
    status: str
    output: Any
    error: Optional[str] = None
    execution_time: float


class AgentTaskResponse(BaseModel):
    """Response for agent task execution"""
    task: str
    success: bool
    final_output: Any
    steps: List[TaskStepResponse]
    review: Optional[Dict[str, Any]] = None
    report: Optional[str] = None
    execution_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    doc_id: str
    chunks_indexed: int
    success: bool
    message: str


class BatchDocumentUploadResponse(BaseModel):
    """Response for batch document upload"""
    total_documents: int
    successful: int
    failed: int
    total_chunks: int
    details: List[DocumentUploadResponse]


class ChatResponse(BaseModel):
    """Response for chat conversation"""
    message: str
    response: str
    session_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    components: Dict[str, str]


class StatsResponse(BaseModel):
    """System statistics response"""
    vector_store: Dict[str, Any]
    tools: List[str]
    uptime: float
