"""
Memory Module - Conversation and Context Management
Maintains state across multiple interactions
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


@dataclass
class Message:
    """Single message in conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """Single conversation turn (user message + agent response)"""
    user_message: Message
    agent_response: Message
    task_context: Optional[Dict[str, Any]] = None


class ConversationMemory:
    """
    Manages conversation history and context
    Implements token-aware memory with sliding window
    """

    def __init__(
        self,
        max_tokens: int = 2000,
        max_turns: int = 10,
        enable_summarization: bool = False
    ):
        """
        Initialize ConversationMemory

        Args:
            max_tokens: Maximum tokens to maintain in memory
            max_turns: Maximum conversation turns to keep
            enable_summarization: Whether to summarize old conversations
        """
        self.max_tokens = max_tokens
        self.max_turns = max_turns
        self.enable_summarization = enable_summarization

        self.messages: List[Message] = []
        self.turns: List[ConversationTurn] = []
        self.context: Dict[str, Any] = {}

        logger.info(f"ConversationMemory initialized (max_tokens={max_tokens}, max_turns={max_turns})")

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add message to memory

        Args:
            role: Message role
            content: Message content
            metadata: Optional metadata

        Returns:
            Message: Created message
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        self.messages.append(message)

        # Trim if necessary
        self._trim_memory()

        return message

    def add_turn(
        self,
        user_content: str,
        agent_content: str,
        task_context: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """
        Add complete conversation turn

        Args:
            user_content: User's message
            agent_content: Agent's response
            task_context: Optional task context

        Returns:
            ConversationTurn: Created turn
        """
        user_msg = Message(role="user", content=user_content)
        agent_msg = Message(role="assistant", content=agent_content)

        turn = ConversationTurn(
            user_message=user_msg,
            agent_response=agent_msg,
            task_context=task_context
        )

        self.turns.append(turn)
        self.messages.extend([user_msg, agent_msg])

        # Trim if necessary
        self._trim_memory()

        return turn

    def get_recent_messages(self, n: int = 5) -> List[Message]:
        """
        Get N most recent messages

        Args:
            n: Number of messages

        Returns:
            List of recent messages
        """
        return self.messages[-n:]

    def get_conversation_history(self) -> str:
        """
        Get formatted conversation history

        Returns:
            str: Formatted conversation history
        """
        lines = []
        for msg in self.messages:
            lines.append(f"{msg.role.upper()}: {msg.content}")
        return "\n".join(lines)

    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get summary of current context

        Returns:
            Dict with context information
        """
        return {
            "total_messages": len(self.messages),
            "total_turns": len(self.turns),
            "context_keys": list(self.context.keys()),
            "estimated_tokens": self._estimate_tokens(),
        }

    def update_context(self, key: str, value: Any):
        """
        Update context variable

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
        logger.debug(f"Context updated: {key}")

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get context variable

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value
        """
        return self.context.get(key, default)

    def clear(self):
        """Clear all memory"""
        self.messages.clear()
        self.turns.clear()
        self.context.clear()
        logger.info("Memory cleared")

    def _estimate_tokens(self) -> int:
        """
        Estimate total tokens in memory (rough approximation)

        Returns:
            int: Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English
        # For Chinese, 1 token ≈ 2 characters
        total_chars = sum(len(msg.content) for msg in self.messages)
        # Use conservative estimate
        return total_chars // 2

    def _trim_memory(self):
        """
        Trim memory to stay within limits
        Removes oldest messages/turns
        """
        # Trim by number of turns
        if len(self.turns) > self.max_turns:
            excess = len(self.turns) - self.max_turns
            logger.info(f"Trimming {excess} old conversation turns")
            self.turns = self.turns[-self.max_turns:]

        # Trim by token count
        estimated_tokens = self._estimate_tokens()
        if estimated_tokens > self.max_tokens:
            # Remove oldest messages until within limit
            while estimated_tokens > self.max_tokens and len(self.messages) > 2:
                removed = self.messages.pop(0)
                estimated_tokens = self._estimate_tokens()
                logger.debug(f"Trimmed message from {removed.role}")

    def export_history(self) -> Dict[str, Any]:
        """
        Export memory to dictionary

        Returns:
            Dict with full memory state
        """
        return {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in self.messages
            ],
            "context": self.context,
            "summary": self.get_context_summary()
        }

    def import_history(self, data: Dict[str, Any]):
        """
        Import memory from dictionary

        Args:
            data: Exported memory data
        """
        self.clear()

        for msg_data in data.get("messages", []):
            self.add_message(
                role=msg_data["role"],
                content=msg_data["content"],
                metadata=msg_data.get("metadata")
            )

        self.context = data.get("context", {})

        logger.info(f"Imported {len(self.messages)} messages")


class TaskMemory:
    """
    Specialized memory for tracking task execution state
    """

    def __init__(self):
        """Initialize TaskMemory"""
        self.current_task: Optional[str] = None
        self.task_history: List[Dict[str, Any]] = []
        self.intermediate_results: Dict[str, Any] = {}

    def start_task(self, task: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Start tracking a new task

        Args:
            task: Task description
            metadata: Optional task metadata
        """
        self.current_task = task
        task_record = {
            "task": task,
            "start_time": datetime.now(),
            "metadata": metadata or {},
            "status": "in_progress"
        }
        self.task_history.append(task_record)
        logger.info(f"Started tracking task: {task}")

    def complete_task(self, result: Any, success: bool = True):
        """
        Mark current task as complete

        Args:
            result: Task result
            success: Whether task succeeded
        """
        if self.task_history:
            self.task_history[-1].update({
                "end_time": datetime.now(),
                "status": "success" if success else "failed",
                "result": result
            })
            logger.info(f"Task completed: {self.current_task}")

        self.current_task = None

    def store_intermediate(self, key: str, value: Any):
        """Store intermediate result"""
        self.intermediate_results[key] = value

    def get_intermediate(self, key: str, default: Any = None) -> Any:
        """Get intermediate result"""
        return self.intermediate_results.get(key, default)

    def clear_intermediates(self):
        """Clear intermediate results"""
        self.intermediate_results.clear()
