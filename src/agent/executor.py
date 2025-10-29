"""
Executor Module - Task Execution Engine
Executes planned steps using registered tools
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from .planner import TaskPlan, TaskStep


class ExecutionStatus(Enum):
    """Status of step execution"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of single step execution"""
    step_id: int
    status: ExecutionStatus
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class ExecutionContext:
    """Context for maintaining state during execution"""

    def __init__(self):
        self.results: Dict[int, StepResult] = {}
        self.intermediate_outputs: Dict[str, Any] = {}

    def add_result(self, result: StepResult):
        """Add step result to context"""
        self.results[result.step_id] = result
        # Store output for future steps to reference
        self.intermediate_outputs[f"step_{result.step_id}"] = result.output

    def get_result(self, step_id: int) -> Optional[StepResult]:
        """Get result of specific step"""
        return self.results.get(step_id)

    def get_output(self, step_id: int) -> Any:
        """Get output of specific step"""
        result = self.get_result(step_id)
        return result.output if result else None

    def all_dependencies_met(self, step: TaskStep) -> bool:
        """Check if all dependencies are successfully executed"""
        for dep_id in step.depends_on:
            result = self.get_result(dep_id)
            if not result or result.status != ExecutionStatus.SUCCESS:
                return False
        return True


class Executor:
    """
    Executor component for executing planned tasks
    Manages tool invocation and result tracking
    """

    def __init__(self, tool_registry: Optional[Dict[str, Any]] = None):
        """
        Initialize Executor

        Args:
            tool_registry: Dictionary mapping tool names to tool instances
        """
        self.tool_registry = tool_registry or {}
        logger.info(f"Executor initialized with {len(self.tool_registry)} tools")

    def register_tool(self, name: str, tool: Any):
        """
        Register a tool for execution

        Args:
            name: Tool name
            tool: Tool instance (should be callable or have an 'invoke' method)
        """
        self.tool_registry[name] = tool
        logger.info(f"Tool registered: {name}")

    def register_tools(self, tools: Dict[str, Any]):
        """
        Register multiple tools

        Args:
            tools: Dictionary of tool name to tool instance
        """
        self.tool_registry.update(tools)
        logger.info(f"Registered {len(tools)} tools")

    async def execute_plan(
        self,
        plan: TaskPlan,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionContext:
        """
        Execute complete task plan

        Args:
            plan: Task plan to execute
            initial_context: Initial context/parameters

        Returns:
            ExecutionContext: Execution context with results

        Raises:
            Exception: If critical execution error occurs
        """
        logger.info(f"Starting execution of plan: {plan.task_description}")

        context = ExecutionContext()
        if initial_context:
            context.intermediate_outputs.update(initial_context)

        # Execute steps in order
        for step in plan.steps:
            result = await self.execute_step(step, context)
            context.add_result(result)

            # Stop execution if critical step fails
            if result.status == ExecutionStatus.FAILED and not self._is_optional_step(step):
                logger.error(f"Critical step {step.step_id} failed, stopping execution")
                # Mark remaining steps as skipped
                self._mark_remaining_skipped(plan, step.step_id, context)
                break

        # Log execution summary
        self._log_execution_summary(context)

        return context

    async def execute_step(
        self,
        step: TaskStep,
        context: ExecutionContext
    ) -> StepResult:
        """
        Execute single step

        Args:
            step: Step to execute
            context: Current execution context

        Returns:
            StepResult: Result of step execution
        """
        import time

        logger.info(f"Executing step {step.step_id}: {step.description}")

        start_time = time.time()

        # Check dependencies
        if not context.all_dependencies_met(step):
            logger.warning(f"Step {step.step_id} dependencies not met, skipping")
            return StepResult(
                step_id=step.step_id,
                status=ExecutionStatus.SKIPPED,
                output=None,
                error="Dependencies not met"
            )

        # Get tool
        tool = self.tool_registry.get(step.tool)
        if not tool:
            logger.error(f"Tool not found: {step.tool}")
            return StepResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                output=None,
                error=f"Tool '{step.tool}' not registered"
            )

        # Prepare parameters (inject outputs from dependencies)
        params = self._prepare_parameters(step, context)

        # Execute tool
        try:
            # Try async invoke first, fall back to sync
            if hasattr(tool, 'ainvoke'):
                output = await tool.ainvoke(params)
            elif hasattr(tool, 'invoke'):
                output = tool.invoke(params)
            elif callable(tool):
                output = tool(**params)
            else:
                raise ValueError(f"Tool '{step.tool}' is not callable")

            execution_time = time.time() - start_time

            logger.info(f"Step {step.step_id} completed successfully in {execution_time:.2f}s")

            return StepResult(
                step_id=step.step_id,
                status=ExecutionStatus.SUCCESS,
                output=output,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Step {step.step_id} failed: {str(e)}")

            return StepResult(
                step_id=step.step_id,
                status=ExecutionStatus.FAILED,
                output=None,
                error=str(e),
                execution_time=execution_time
            )

    def _prepare_parameters(
        self,
        step: TaskStep,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Prepare parameters for step execution

        Injects outputs from dependency steps if needed

        Args:
            step: Current step
            context: Execution context

        Returns:
            Dict with prepared parameters
        """
        params = step.parameters.copy()

        # Inject dependency outputs
        for dep_id in step.depends_on:
            dep_output = context.get_output(dep_id)
            # Use a convention: dependency outputs available as step_{id}_output
            params[f"step_{dep_id}_output"] = dep_output

        # Add all intermediate outputs for potential reference
        params["context"] = context.intermediate_outputs

        return params

    def _is_optional_step(self, step: TaskStep) -> bool:
        """Check if step is optional (can be determined by parameters or action)"""
        return step.parameters.get("optional", False)

    def _mark_remaining_skipped(
        self,
        plan: TaskPlan,
        failed_step_id: int,
        context: ExecutionContext
    ):
        """Mark all remaining steps as skipped after failure"""
        for step in plan.steps:
            if step.step_id > failed_step_id and step.step_id not in context.results:
                context.add_result(StepResult(
                    step_id=step.step_id,
                    status=ExecutionStatus.SKIPPED,
                    output=None,
                    error="Previous step failed"
                ))

    def _log_execution_summary(self, context: ExecutionContext):
        """Log summary of execution"""
        total = len(context.results)
        success = sum(1 for r in context.results.values() if r.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for r in context.results.values() if r.status == ExecutionStatus.FAILED)
        skipped = sum(1 for r in context.results.values() if r.status == ExecutionStatus.SKIPPED)

        logger.info(f"Execution summary: {total} steps - {success} success, {failed} failed, {skipped} skipped")
