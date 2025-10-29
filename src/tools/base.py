"""
Base Tool Classes and Tool Registry
Defines the interface for all tools in the system
"""
from typing import Any, Dict, Optional, Callable
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from loguru import logger


class ToolInput(BaseModel):
    """Base class for tool input validation"""
    pass


class ToolOutput(BaseModel):
    """Base class for tool output"""
    success: bool = Field(description="Whether tool execution succeeded")
    data: Any = Field(description="Tool output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseTool(ABC):
    """
    Abstract base class for all tools

    All tools must implement:
    - name: Unique tool identifier
    - description: Human-readable description
    - invoke: Synchronous execution method
    - ainvoke: Asynchronous execution method (optional)
    """

    def __init__(self, name: str, description: str):
        """
        Initialize base tool

        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description

    @abstractmethod
    def invoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Execute tool synchronously

        Args:
            input_data: Input parameters

        Returns:
            ToolOutput: Tool execution result
        """
        pass

    async def ainvoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Execute tool asynchronously

        Default implementation calls sync invoke
        Override for true async execution

        Args:
            input_data: Input parameters

        Returns:
            ToolOutput: Tool execution result
        """
        return self.invoke(input_data)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid
        """
        # Override in subclass for custom validation
        return True

    def __call__(self, **kwargs) -> ToolOutput:
        """
        Make tool callable

        Args:
            **kwargs: Input parameters

        Returns:
            ToolOutput: Tool execution result
        """
        return self.invoke(kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export tool metadata

        Returns:
            Dict with tool information
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__
        }


class ToolRegistry:
    """
    Central registry for managing tools

    Provides tool registration, lookup, and management
    """

    def __init__(self):
        """Initialize tool registry"""
        self._tools: Dict[str, BaseTool] = {}
        logger.info("Tool registry initialized")

    def register(self, tool: BaseTool):
        """
        Register a tool

        Args:
            tool: Tool to register

        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")

        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def register_function(
        self,
        name: str,
        description: str,
        func: Callable
    ):
        """
        Register a simple function as a tool

        Args:
            name: Tool name
            description: Tool description
            func: Function to wrap as tool
        """
        tool = FunctionTool(name, description, func)
        self.register(tool)

    def unregister(self, name: str):
        """
        Unregister a tool

        Args:
            name: Tool name

        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")

        del self._tools[name]
        logger.info(f"Unregistered tool: {name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """
        Get tool by name

        Args:
            name: Tool name

        Returns:
            BaseTool or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, str]:
        """
        List all registered tools

        Returns:
            Dict mapping tool names to descriptions
        """
        return {
            name: tool.description
            for name, tool in self._tools.items()
        }

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools

        Returns:
            Dict of all tools
        """
        return self._tools.copy()

    def clear(self):
        """Clear all registered tools"""
        self._tools.clear()
        logger.info("Tool registry cleared")

    def __len__(self) -> int:
        """Get number of registered tools"""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool is registered"""
        return name in self._tools


class FunctionTool(BaseTool):
    """
    Wrapper to convert a simple function into a tool
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable
    ):
        """
        Initialize function tool

        Args:
            name: Tool name
            description: Tool description
            func: Function to wrap
        """
        super().__init__(name, description)
        self.func = func

    def invoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Execute wrapped function

        Args:
            input_data: Input parameters

        Returns:
            ToolOutput: Tool execution result
        """
        try:
            result = self.func(**input_data)

            return ToolOutput(
                success=True,
                data=result
            )

        except Exception as e:
            logger.error(f"Tool '{self.name}' execution failed: {str(e)}")
            return ToolOutput(
                success=False,
                data=None,
                error=str(e)
            )


# Global tool registry instance
tool_registry = ToolRegistry()
