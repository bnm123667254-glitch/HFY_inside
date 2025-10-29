"""
Reviewer Module - Result Validation and Quality Check
Validates execution results and ensures quality standards
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger

from .executor import ExecutionContext, ExecutionStatus
from .planner import TaskPlan


class ReviewResult(BaseModel):
    """Result of task execution review"""
    passed: bool = Field(description="Whether the execution meets quality standards")
    quality_score: float = Field(description="Quality score (0-1)", ge=0, le=1)
    completeness_score: float = Field(description="Completeness score (0-1)", ge=0, le=1)
    issues: List[str] = Field(default_factory=list, description="List of identified issues")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    summary: str = Field(description="Summary of review")


class Reviewer:
    """
    Reviewer component for validating execution results
    Ensures output quality and task completion
    """

    REVIEW_PROMPT = """You are a quality reviewer for an AI agent execution system.
Your task is to review the execution results and assess whether the task was completed successfully and meets quality standards.

Original Task: {task_description}

Execution Plan:
{plan_summary}

Execution Results:
{execution_results}

Evaluate the following aspects:
1. **Completeness**: Were all necessary steps executed? Was the original task fully addressed?
2. **Quality**: Is the output accurate, relevant, and well-formatted?
3. **Correctness**: Are there any errors or inconsistencies in the results?

{format_instructions}

Provide a detailed review as a JSON object.
"""

    def __init__(self, llm: BaseChatModel):
        """
        Initialize Reviewer

        Args:
            llm: Language model for review
        """
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=ReviewResult)

        # Create review prompt template
        self.prompt = ChatPromptTemplate.from_template(self.REVIEW_PROMPT)

        # Create review chain
        self.chain = self.prompt | self.llm | self.parser

        logger.info("Reviewer initialized successfully")

    async def review(
        self,
        plan: TaskPlan,
        context: ExecutionContext
    ) -> ReviewResult:
        """
        Review execution results

        Args:
            plan: Original task plan
            context: Execution context with results

        Returns:
            ReviewResult: Review result with quality assessment

        Raises:
            Exception: If review fails
        """
        logger.info("Starting execution review")

        try:
            # Prepare execution summary
            plan_summary = self._format_plan_summary(plan)
            execution_results = self._format_execution_results(context)

            # Prepare input
            input_data = {
                "task_description": plan.task_description,
                "plan_summary": plan_summary,
                "execution_results": execution_results,
                "format_instructions": self.parser.get_format_instructions()
            }

            # Execute review chain
            result = await self.chain.ainvoke(input_data)

            # Convert to ReviewResult if it's a dict
            if isinstance(result, dict):
                review = ReviewResult(**result)
            else:
                review = result

            logger.info(f"Review completed - Passed: {review.passed}, Quality: {review.quality_score:.2f}")

            return review

        except Exception as e:
            logger.error(f"Review failed: {str(e)}")
            # Return a default failed review
            return ReviewResult(
                passed=False,
                quality_score=0.0,
                completeness_score=0.0,
                issues=[f"Review process failed: {str(e)}"],
                recommendations=["Manual inspection required"],
                summary="Automated review failed"
            )

    def quick_review(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Perform quick rule-based review without LLM

        Args:
            context: Execution context with results

        Returns:
            Dict with basic review metrics
        """
        total_steps = len(context.results)
        successful_steps = sum(
            1 for r in context.results.values()
            if r.status == ExecutionStatus.SUCCESS
        )
        failed_steps = sum(
            1 for r in context.results.values()
            if r.status == ExecutionStatus.FAILED
        )

        success_rate = successful_steps / total_steps if total_steps > 0 else 0

        passed = failed_steps == 0 and successful_steps > 0

        return {
            "passed": passed,
            "success_rate": success_rate,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "execution_time": sum(r.execution_time for r in context.results.values())
        }

    def _format_plan_summary(self, plan: TaskPlan) -> str:
        """Format plan summary for review"""
        lines = [f"Total steps: {len(plan.steps)}"]
        for step in plan.steps:
            lines.append(f"  {step.step_id}. {step.description} (Tool: {step.tool})")
        return "\n".join(lines)

    def _format_execution_results(self, context: ExecutionContext) -> str:
        """Format execution results for review"""
        lines = []
        for step_id, result in sorted(context.results.items()):
            status_icon = "✓" if result.status == ExecutionStatus.SUCCESS else "✗"
            lines.append(f"{status_icon} Step {step_id}: {result.status.value}")

            if result.error:
                lines.append(f"    Error: {result.error}")

            # Include truncated output preview
            if result.output:
                output_preview = str(result.output)[:200]
                if len(str(result.output)) > 200:
                    output_preview += "..."
                lines.append(f"    Output: {output_preview}")

            lines.append(f"    Time: {result.execution_time:.2f}s")

        return "\n".join(lines)

    def generate_report(
        self,
        plan: TaskPlan,
        context: ExecutionContext,
        review: ReviewResult
    ) -> str:
        """
        Generate comprehensive execution report

        Args:
            plan: Original task plan
            context: Execution context
            review: Review result

        Returns:
            str: Formatted report
        """
        report_lines = [
            "=" * 60,
            "AGENT EXECUTION REPORT",
            "=" * 60,
            "",
            f"Task: {plan.task_description}",
            f"Complexity: {plan.estimated_complexity}",
            "",
            "EXECUTION SUMMARY",
            "-" * 60,
        ]

        # Add quick metrics
        metrics = self.quick_review(context)
        report_lines.extend([
            f"Total Steps: {metrics['total_steps']}",
            f"Successful: {metrics['successful_steps']}",
            f"Failed: {metrics['failed_steps']}",
            f"Success Rate: {metrics['success_rate']:.1%}",
            f"Total Time: {metrics['execution_time']:.2f}s",
            "",
        ])

        # Add review results
        report_lines.extend([
            "QUALITY REVIEW",
            "-" * 60,
            f"Status: {'PASSED' if review.passed else 'FAILED'}",
            f"Quality Score: {review.quality_score:.2f}",
            f"Completeness Score: {review.completeness_score:.2f}",
            "",
            f"Summary: {review.summary}",
            "",
        ])

        # Add issues if any
        if review.issues:
            report_lines.extend([
                "Issues Identified:",
                *[f"  - {issue}" for issue in review.issues],
                "",
            ])

        # Add recommendations if any
        if review.recommendations:
            report_lines.extend([
                "Recommendations:",
                *[f"  - {rec}" for rec in review.recommendations],
                "",
            ])

        # Add detailed step results
        report_lines.extend([
            "DETAILED STEP RESULTS",
            "-" * 60,
        ])

        for step_id, result in sorted(context.results.items()):
            report_lines.extend([
                f"Step {step_id}: {result.status.value.upper()}",
                f"  Time: {result.execution_time:.2f}s",
            ])

            if result.error:
                report_lines.append(f"  Error: {result.error}")

            report_lines.append("")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)
