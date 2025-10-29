"""
Planner Module - Task Planning and Decomposition
Uses JSON Schema to ensure structured LLM output
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger


class TaskStep(BaseModel):
    """Single step in task execution plan"""
    step_id: int = Field(description="Step identifier")
    action: str = Field(description="Action to perform (e.g., 'search', 'summarize', 'generate')")
    tool: str = Field(description="Tool name to use for this step")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")
    description: str = Field(description="Human-readable description of this step")
    depends_on: List[int] = Field(default_factory=list, description="Step IDs this step depends on")


class TaskPlan(BaseModel):
    """Complete task execution plan"""
    task_description: str = Field(description="Original task description")
    steps: List[TaskStep] = Field(description="Ordered list of execution steps")
    estimated_complexity: str = Field(
        description="Estimated complexity (low/medium/high)",
        default="medium"
    )


class Planner:
    """
    Planner component for task decomposition and planning
    Implements structured output using JSON Schema
    """

    PLANNING_PROMPT = """You are an intelligent task planner for a compliance Q&A system.
Given a user's task, decompose it into a sequence of executable steps.

Available tools:
- knowledge_search: Search compliance documents for relevant information
- document_summarize: Summarize compliance documents or search results
- email_draft: Generate email draft based on provided content
- compliance_check: Check compliance requirements for specific scenarios
- report_generate: Generate compliance report

Task: {task}

Previous context (if any): {context}

Create a detailed execution plan. Each step should:
1. Have a unique step_id (starting from 1)
2. Specify the tool to use
3. Include necessary parameters
4. Have clear dependencies on previous steps

{format_instructions}

Return a valid JSON object with the task plan.
"""

    def __init__(self, llm: BaseChatModel):
        """
        Initialize Planner

        Args:
            llm: Language model for planning
        """
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=TaskPlan)

        # Create planning prompt template
        self.prompt = ChatPromptTemplate.from_template(self.PLANNING_PROMPT)

        # Create planning chain
        self.chain = self.prompt | self.llm | self.parser

        logger.info("Planner initialized successfully")

    async def plan(
        self,
        task: str,
        context: Optional[str] = None
    ) -> TaskPlan:
        """
        Create execution plan for given task

        Args:
            task: User's task description
            context: Optional context from previous interactions

        Returns:
            TaskPlan: Structured task execution plan

        Raises:
            Exception: If planning fails
        """
        logger.info(f"Planning task: {task}")

        try:
            # Prepare input
            input_data = {
                "task": task,
                "context": context or "No previous context",
                "format_instructions": self.parser.get_format_instructions()
            }

            # Execute planning chain
            result = await self.chain.ainvoke(input_data)

            # Convert to TaskPlan if it's a dict
            if isinstance(result, dict):
                plan = TaskPlan(**result)
            else:
                plan = result

            logger.info(f"Task plan created with {len(plan.steps)} steps")
            logger.debug(f"Plan details: {plan.model_dump_json(indent=2)}")

            return plan

        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            raise

    def validate_plan(self, plan: TaskPlan) -> bool:
        """
        Validate task plan for consistency

        Args:
            plan: Task plan to validate

        Returns:
            bool: True if plan is valid
        """
        # Check if all dependency step_ids exist
        step_ids = {step.step_id for step in plan.steps}

        for step in plan.steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    logger.error(f"Invalid dependency: step {step.step_id} depends on non-existent step {dep_id}")
                    return False

                # Check that dependencies are before current step
                if dep_id >= step.step_id:
                    logger.error(f"Invalid dependency order: step {step.step_id} depends on later step {dep_id}")
                    return False

        logger.info("Plan validation successful")
        return True

    def optimize_plan(self, plan: TaskPlan) -> TaskPlan:
        """
        Optimize task plan by identifying parallel execution opportunities

        Args:
            plan: Original task plan

        Returns:
            TaskPlan: Optimized plan
        """
        # This is a placeholder for future optimization logic
        # Could identify steps that can run in parallel
        return plan
