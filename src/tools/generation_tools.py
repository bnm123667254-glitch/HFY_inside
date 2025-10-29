"""
Generation Tools - Content Generation
Provides email drafting and report generation
"""
from typing import Dict, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from .base import BaseTool, ToolOutput


class EmailDraftTool(BaseTool):
    """
    Tool for generating email drafts

    Creates professional emails based on provided content
    """

    EMAIL_DRAFT_PROMPT = """You are a professional business email writer. Generate an email draft based on the following information.

Purpose: {purpose}

Key Content:
{content}

Recipient Type: {recipient_type}

Requirements:
1. Professional and polite tone
2. Clear subject line
3. Well-structured body with appropriate greeting and closing
4. Include key information from the content
5. Keep it concise and actionable

Generate the email in Chinese with the following format:
---
Subject: [subject line]

[Email body with greeting, main content, and closing]
---
"""

    def __init__(
        self,
        llm: BaseChatModel,
        name: str = "email_draft",
        description: str = "Generate email draft based on provided content"
    ):
        """
        Initialize email draft tool

        Args:
            llm: Language model
            name: Tool name
            description: Tool description
        """
        super().__init__(name, description)
        self.llm = llm

        self.prompt = ChatPromptTemplate.from_template(self.EMAIL_DRAFT_PROMPT)

    def invoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Generate email draft

        Args:
            input_data: Must contain 'content', optionally 'purpose' and 'recipient_type'

        Returns:
            ToolOutput with email draft
        """
        try:
            content = input_data.get("content")

            # Try to get content from previous step if not directly provided
            if not content:
                step_output = input_data.get("context", {})
                for key, value in step_output.items():
                    if key.endswith("_output") and isinstance(value, dict):
                        content = value.get("data", {}).get("summary") or \
                                  value.get("data", {}).get("analysis")
                        if content:
                            break

            if not content:
                return ToolOutput(
                    success=False,
                    data=None,
                    error="Missing 'content' parameter"
                )

            purpose = input_data.get("purpose", "分享合规信息")
            recipient_type = input_data.get("recipient_type", "同事")

            logger.info("Generating email draft")

            # Generate email
            messages = self.prompt.format_messages(
                purpose=purpose,
                content=str(content)[:2000],  # Limit content length
                recipient_type=recipient_type
            )

            response = self.llm.invoke(messages)
            email_draft = response.content

            return ToolOutput(
                success=True,
                data={
                    "email_draft": email_draft,
                    "purpose": purpose,
                    "recipient_type": recipient_type
                },
                metadata={
                    "tool": self.name
                }
            )

        except Exception as e:
            logger.error(f"Email draft generation failed: {str(e)}")
            return ToolOutput(
                success=False,
                data=None,
                error=str(e)
            )


class ReportGenerateTool(BaseTool):
    """
    Tool for generating compliance reports

    Creates structured reports from provided information
    """

    REPORT_PROMPT = """You are a compliance report writer. Generate a comprehensive compliance report based on the following information.

Report Type: {report_type}

Source Information:
{source_content}

Additional Context: {additional_context}

Generate a well-structured report in Chinese including:
1. Executive Summary (执行摘要)
2. Detailed Findings (详细发现)
3. Compliance Assessment (合规评估)
4. Recommendations (建议)
5. Conclusion (结论)

Use clear headings, bullet points, and professional language. Make it actionable and comprehensive.
"""

    def __init__(
        self,
        llm: BaseChatModel,
        name: str = "report_generate",
        description: str = "Generate compliance report"
    ):
        """
        Initialize report generation tool

        Args:
            llm: Language model
            name: Tool name
            description: Tool description
        """
        super().__init__(name, description)
        self.llm = llm

        self.prompt = ChatPromptTemplate.from_template(self.REPORT_PROMPT)

    def invoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Generate compliance report

        Args:
            input_data: Must contain source content, optionally 'report_type'

        Returns:
            ToolOutput with generated report
        """
        try:
            # Try to extract source content from various possible inputs
            source_content = input_data.get("content") or input_data.get("source_content")

            if not source_content:
                # Try to get from previous step outputs
                step_output = input_data.get("context", {})
                for key, value in step_output.items():
                    if key.endswith("_output") and isinstance(value, dict):
                        source_content = value.get("data", {}).get("summary") or \
                                       value.get("data", {}).get("analysis") or \
                                       value.get("data", {}).get("results")
                        if source_content:
                            break

            if not source_content:
                return ToolOutput(
                    success=False,
                    data=None,
                    error="Missing source content for report generation"
                )

            report_type = input_data.get("report_type", "合规审查报告")
            additional_context = input_data.get("additional_context", "")

            logger.info(f"Generating {report_type}")

            # Format source content
            if isinstance(source_content, list):
                formatted_content = "\n\n".join([str(item) for item in source_content])
            else:
                formatted_content = str(source_content)

            # Generate report
            messages = self.prompt.format_messages(
                report_type=report_type,
                source_content=formatted_content[:3000],  # Limit length
                additional_context=additional_context
            )

            response = self.llm.invoke(messages)
            report = response.content

            return ToolOutput(
                success=True,
                data={
                    "report": report,
                    "report_type": report_type
                },
                metadata={
                    "tool": self.name
                }
            )

        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return ToolOutput(
                success=False,
                data=None,
                error=str(e)
            )


class SummaryEnhanceTool(BaseTool):
    """
    Tool for enhancing and reformatting summaries

    Improves readability and structure of existing summaries
    """

    ENHANCE_PROMPT = """You are an expert editor. Enhance and reformat the following summary to make it more clear, concise, and actionable.

Original Summary:
{original_summary}

Requirements:
1. Improve clarity and readability
2. Use bullet points for key items
3. Highlight important compliance requirements
4. Add clear section headings
5. Ensure professional tone
6. Keep it concise yet comprehensive

Enhanced summary in Chinese:
"""

    def __init__(
        self,
        llm: BaseChatModel,
        name: str = "summary_enhance",
        description: str = "Enhance and reformat summaries for better clarity"
    ):
        """
        Initialize summary enhance tool

        Args:
            llm: Language model
            name: Tool name
            description: Tool description
        """
        super().__init__(name, description)
        self.llm = llm

        self.prompt = ChatPromptTemplate.from_template(self.ENHANCE_PROMPT)

    def invoke(self, input_data: Dict[str, Any]) -> ToolOutput:
        """
        Enhance summary

        Args:
            input_data: Must contain 'summary' or extract from previous steps

        Returns:
            ToolOutput with enhanced summary
        """
        try:
            original_summary = input_data.get("summary")

            if not original_summary:
                # Try to get from previous step
                step_output = input_data.get("context", {})
                for key, value in step_output.items():
                    if key.endswith("_output") and isinstance(value, dict):
                        original_summary = value.get("data", {}).get("summary")
                        if original_summary:
                            break

            if not original_summary:
                return ToolOutput(
                    success=False,
                    data=None,
                    error="Missing 'summary' parameter"
                )

            logger.info("Enhancing summary")

            # Enhance summary
            messages = self.prompt.format_messages(
                original_summary=str(original_summary)[:2000]
            )

            response = self.llm.invoke(messages)
            enhanced_summary = response.content

            return ToolOutput(
                success=True,
                data={
                    "enhanced_summary": enhanced_summary,
                    "original_length": len(str(original_summary)),
                    "enhanced_length": len(enhanced_summary)
                },
                metadata={
                    "tool": self.name
                }
            )

        except Exception as e:
            logger.error(f"Summary enhancement failed: {str(e)}")
            return ToolOutput(
                success=False,
                data=None,
                error=str(e)
            )
