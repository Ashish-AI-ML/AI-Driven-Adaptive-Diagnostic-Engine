"""
LLM Client — async OpenAI client with exponential backoff retry logic.
"""

import json
import asyncio
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings


class LLMClient:
    """Async LLM client with retry logic and JSON parsing."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL

    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        max_tokens: int = 600,
    ) -> dict:
        """
        Call the LLM with exponential backoff retry.

        Args:
            system_prompt: System-level instructions.
            user_prompt: User-level prompt with data.
            max_retries: Maximum number of retry attempts.
            max_tokens: Maximum tokens in response.

        Returns:
            Parsed JSON dictionary from the LLM response.

        Raises:
            Exception: If all retries fail.
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content
                return self._parse_json_response(content)

            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s
                    await asyncio.sleep(wait_time)

        raise Exception(
            f"LLM API failed after {max_retries} attempts: {str(last_exception)}"
        )

    @staticmethod
    def _parse_json_response(content: str) -> dict:
        """
        Parse JSON from LLM response.
        Handles cases where the response might be wrapped in markdown code blocks.
        """
        # Strip markdown code block markers if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Return raw text wrapped in a fallback structure
            return {
                "step_1": {"focus": "Review", "action": content[:200], "resource_type": "Study Guide"},
                "step_2": {"focus": "Practice", "action": "Complete practice problems", "resource_type": "Practice Set"},
                "step_3": {"focus": "Assessment", "action": "Take a timed practice test", "resource_type": "Timed Mock Test"},
            }
