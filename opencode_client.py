from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import os
import json
import asyncio
from typing import Any, Dict, List, Optional

load_dotenv()

class OpenCodeClient:
    """
    Fully automated OpenCode → Claude integration.
    Sends prompts to the OpenCode model and returns structured file edits.
    """

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is missing. Add it to your .env file.")

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-6"
        self.system_prompt = (
            "You are OpenCode. Always return ONLY valid JSON. "
            "Never include explanations, comments, or text outside the JSON array."
        )

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    async def generate_file_edits(self, prompt: str) -> List[Dict[str, Any]]:
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                )

                raw = response.content[0].text.strip()

                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    cleaned = self._extract_json(raw)
                    return json.loads(cleaned)

            except Exception as ex:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"OpenCode failed after {max_attempts} attempts: {ex}"
                    )
                await asyncio.sleep(1.0)

        raise RuntimeError("Unexpected failure in generate_file_edits")

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _extract_json(self, text: str) -> str:
        """
        Extracts the first JSON array from the text.
        Useful if Claude wraps JSON in markdown fences or adds stray characters.
        """
        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1:
            raise ValueError("No JSON array found in OpenCode output")

        return text[start : end + 1]


# ---------------------------------------------------------
# Convenience function for orchestrator
# ---------------------------------------------------------
async def call_opencode(prompt: str) -> List[Dict[str, Any]]:
    client = OpenCodeClient()
    return await client.generate_file_edits(prompt)
