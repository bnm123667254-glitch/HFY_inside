"""
Test cases for Agent Framework
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.agent import Planner, Executor, Reviewer, ComplianceAgent, TaskPlan, TaskStep
from src.models import get_llm


class TestPlanner:
    """Test Planner component"""

    @pytest.fixture
    def planner(self):
        """Create planner fixture"""
        llm = Mock()
        return Planner(llm)

    def test_planner_initialization(self, planner):
        """Test planner initializes correctly"""
        assert planner.llm is not None
        assert planner.parser is not None

    @pytest.mark.asyncio
    async def test_plan_validation(self, planner):
        """Test plan validation logic"""
        # Valid plan
        plan = TaskPlan(
            task_description="Test task",
            steps=[
                TaskStep(
                    step_id=1,
                    action="search",
                    tool="knowledge_search",
                    parameters={},
                    description="Search knowledge",
                    depends_on=[]
                ),
                TaskStep(
                    step_id=2,
                    action="summarize",
                    tool="document_summarize",
                    parameters={},
                    description="Summarize results",
                    depends_on=[1]
                )
            ],
            estimated_complexity="medium"
        )

        assert planner.validate_plan(plan) is True

        # Invalid plan (circular dependency)
        invalid_plan = TaskPlan(
            task_description="Test task",
            steps=[
                TaskStep(
                    step_id=1,
                    action="search",
                    tool="knowledge_search",
                    parameters={},
                    description="Search",
                    depends_on=[2]  # Depends on later step
                ),
                TaskStep(
                    step_id=2,
                    action="summarize",
                    tool="document_summarize",
                    parameters={},
                    description="Summarize",
                    depends_on=[1]
                )
            ]
        )

        assert planner.validate_plan(invalid_plan) is False


class TestExecutor:
    """Test Executor component"""

    @pytest.fixture
    def executor(self):
        """Create executor fixture"""
        return Executor()

    def test_executor_initialization(self, executor):
        """Test executor initializes correctly"""
        assert executor.tool_registry is not None
        assert len(executor.tool_registry) == 0

    def test_tool_registration(self, executor):
        """Test tool registration"""
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        executor.register_tool("test_tool", mock_tool)

        assert "test_tool" in executor.tool_registry
        assert executor.tool_registry["test_tool"] == mock_tool


class TestComplianceAgent:
    """Test ComplianceAgent integration"""

    @pytest.fixture
    def agent(self):
        """Create agent fixture"""
        llm = Mock()
        return ComplianceAgent(llm, enable_review=False)

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.planner is not None
        assert agent.executor is not None
        assert agent.reviewer is None  # Disabled

    def test_tool_registration(self, agent):
        """Test tool registration through agent"""
        mock_tool = Mock()
        agent.register_tool("test_tool", mock_tool)

        assert "test_tool" in agent.executor.tool_registry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
