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
    Sends prompts to the model and returns structured file edits.
    """

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is missing. Add it to your .env file.")

        self.client = AsyncAnthropic(api_key=api_key)

        # Your workspace supports Claude 4 models
        self.model = "claude-sonnet-4-6"

        # STRONG system prompt — absolutely required
        self.system_prompt = (
            "You are OpenCode. You ALWAYS return ONLY a JSON array of file edits.\n"
            "Never include explanations, comments, markdown, or text outside the JSON array.\n"
            "If no edits are needed, return an empty JSON array: [].\n"
            "Each edit must include: \"file\", \"instructions\", and \"content\".\n"
            "Your output must ALWAYS be valid JSON."
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

                # Debug logging (optional)
                print("\n--- RAW CLAUDE OUTPUT ---")
                print(raw)
                print("--- END RAW OUTPUT ---\n")

                # Handle empty output
                if not raw:
                    return []

                # First attempt: direct JSON
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    pass

                # Second attempt: repair JSON
                cleaned = self._repair_json(raw)
                return json.loads(cleaned)

            except Exception as ex:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"OpenCode failed after {max_attempts} attempts: {ex}"
                    )
                await asyncio.sleep(1.0)

        raise RuntimeError("Unexpected failure in generate_file_edits")

    # ---------------------------------------------------------
    # JSON Repair Helpers
    # ---------------------------------------------------------
    def _repair_json(self, text: str) -> str:
        """
        Attempts to extract or repair JSON arrays from Claude output.
        Handles:
        - Markdown fences
        - Leading/trailing prose
        - Single-object JSON (wraps in array)
        """

        # Remove markdown fences
        if "```" in text:
            parts = text.split("```")
            # Try to find the JSON-looking part
            for p in parts:
                if "[" in p or "{" in p:
                    text = p.strip()
                    break

        # Extract array if present
        if "[" in text and "]" in text:
            start = text.find("[")
            end = text.rfind("]") + 1
            return text[start:end]

        # If it's a single object, wrap it
        if text.strip().startswith("{") and text.strip().endswith("}"):
            return f"[{text}]"

        raise ValueError("No JSON array found in OpenCode output")

# ---------------------------------------------------------
# Convenience function for orchestrator
# ---------------------------------------------------------
async def call_opencode(prompt: str) -> List[Dict[str, Any]]:
    client = OpenCodeClient()
    return await client.generate_file_edits(prompt)
