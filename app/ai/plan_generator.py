"""
Plan Generator — orchestrates prompt building, LLM calling, and result storage.
Idempotent: returns cached plan if already generated for the session.
"""

from app.ai.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from app.ai.llm_client import LLMClient


class PlanGenerator:
    """Orchestrates AI study plan generation."""

    def __init__(self):
        self.llm_client = LLMClient()

    async def generate(self, test_result: dict) -> dict:
        """
        Generate a personalized study plan from test results.

        Flow:
        1. Build prompts from test result data
        2. Call LLM
        3. Return parsed plan

        Args:
            test_result: TestResult document from MongoDB.

        Returns:
            Study plan dictionary with step_1, step_2, step_3.
        """
        # Build prompts
        user_prompt = build_user_prompt(test_result)

        # Call LLM
        plan = await self.llm_client.generate_completion(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return plan
