"""
Main Agent Controller - Orchestrates Planner, Executor, and Reviewer
Implements the complete P-E-R (Planner-Executor-Reviewer) workflow
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.language_models import BaseChatModel
from loguru import logger

from .planner import Planner, TaskPlan
from .executor import Executor, ExecutionContext
from .reviewer import Reviewer, ReviewResult


@dataclass
class AgentResult:
    """Complete result from agent execution"""
    task: str
    plan: TaskPlan
    execution_context: ExecutionContext
    review: ReviewResult
    success: bool
    final_output: Any
    report: str


class ComplianceAgent:
    """
    Main Agent Controller implementing P-E-R framework

    Architecture:
    1. Planner: Decomposes task into executable steps
    2. Executor: Executes steps using registered tools
    3. Reviewer: Validates results and ensures quality
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Optional[Dict[str, Any]] = None,
        enable_review: bool = True
    ):
        """
        Initialize ComplianceAgent

        Args:
            llm: Language model for planning and review
            tools: Dictionary of available tools
            enable_review: Whether to enable reviewer (can disable for faster execution)
        """
        self.llm = llm
        self.enable_review = enable_review

        # Initialize components
        self.planner = Planner(llm)
        self.executor = Executor(tools)
        self.reviewer = Reviewer(llm) if enable_review else None

        logger.info("ComplianceAgent initialized with P-E-R framework")

    async def run(
        self,
        task: str,
        context: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Execute complete agent workflow

        Args:
            task: User's task description
            context: Optional context from previous interactions
            parameters: Optional initial parameters

        Returns:
            AgentResult: Complete execution result

        Raises:
            Exception: If critical failure occurs
        """
        logger.info(f"Starting agent execution for task: {task}")

        try:
            # Phase 1: Planning
            logger.info("Phase 1: Planning")
            plan = await self.planner.plan(task, context)

            # Validate plan
            if not self.planner.validate_plan(plan):
                raise ValueError("Generated plan is invalid")

            # Phase 2: Execution
            logger.info("Phase 2: Execution")
            execution_context = await self.executor.execute_plan(plan, parameters)

            # Phase 3: Review
            if self.enable_review and self.reviewer:
                logger.info("Phase 3: Review")
                review = await self.reviewer.review(plan, execution_context)
            else:
                # Create basic review from quick metrics
                metrics = self.executor._log_execution_summary.__self__.quick_review(execution_context) \
                    if hasattr(self.executor._log_execution_summary, '__self__') else {}
                review = ReviewResult(
                    passed=True,
                    quality_score=1.0,
                    completeness_score=1.0,
                    summary="Review skipped (disabled)"
                )

            # Extract final output (from last successful step)
            final_output = self._extract_final_output(execution_context)

            # Generate report
            if self.reviewer:
                report = self.reviewer.generate_report(plan, execution_context, review)
            else:
                report = "Report generation skipped (reviewer disabled)"

            # Determine overall success
            success = review.passed

            logger.info(f"Agent execution completed - Success: {success}")

            return AgentResult(
                task=task,
                plan=plan,
                execution_context=execution_context,
                review=review,
                success=success,
                final_output=final_output,
                report=report
            )

        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            raise

    def _extract_final_output(self, context: ExecutionContext) -> Any:
        """
        Extract final output from execution context

        Args:
            context: Execution context

        Returns:
            Final output (from last successful step)
        """
        # Find last successful step
        for step_id in sorted(context.results.keys(), reverse=True):
            result = context.results[step_id]
            if result.status.value == "success":
                return result.output

        return None

    def register_tool(self, name: str, tool: Any):
        """
        Register a tool with the executor

        Args:
            name: Tool name
            tool: Tool instance
        """
        self.executor.register_tool(name, tool)

    def register_tools(self, tools: Dict[str, Any]):
        """
        Register multiple tools

        Args:
            tools: Dictionary of tools
        """
        self.executor.register_tools(tools)


class AgentFactory:
    """Factory for creating pre-configured agents"""

    @staticmethod
    def create_compliance_agent(
        llm: BaseChatModel,
        enable_review: bool = True
    ) -> ComplianceAgent:
        """
        Create agent for compliance Q&A tasks

        Args:
            llm: Language model
            enable_review: Enable review phase

        Returns:
            ComplianceAgent: Configured agent
        """
        agent = ComplianceAgent(llm, enable_review=enable_review)
        logger.info("Created compliance agent")
        return agent

    @staticmethod
    def create_agent_with_tools(
        llm: BaseChatModel,
        tools: Dict[str, Any],
        enable_review: bool = True
    ) -> ComplianceAgent:
        """
        Create agent with pre-registered tools

        Args:
            llm: Language model
            tools: Tools to register
            enable_review: Enable review phase

        Returns:
            ComplianceAgent: Configured agent with tools
        """
        agent = ComplianceAgent(llm, tools=tools, enable_review=enable_review)
        logger.info(f"Created agent with {len(tools)} tools")
        return agent
