from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import os
import json
import asyncio

from utils.json_extractor import JsonExtractor
from utils.json_sanitizer import JsonSanitizer
from utils.json_validator import JsonValidator
from model_constants import CLAUDE_HAIKU

load_dotenv()


class OpenCodeClient:
    """
    Claude → OpenCode client.
    Supports:
    - File edits (strict JSON array of edits)
    - Generic JSON subtasks (planning/decomposition)
    Uses hardened JSON pipeline.
    """

    def __init__(self, api_key=None, model=None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is missing")

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model or CLAUDE_HAIKU

        # File-edit prompt
        self.file_prompt = (
            "You are OpenCode. You ALWAYS return ONLY a JSON array of file edits.\n"
            "Never include explanations, comments, markdown, or text outside the JSON array.\n"
            "If no edits are needed, return [].\n"
            "Each edit must include: \"file\", \"instructions\", and \"content\".\n"
            "Your output must ALWAYS be valid JSON."
        )

        # Generic JSON prompt (planning/decomposition)
        self.json_prompt = (
            "You ALWAYS return ONLY a JSON array.\n"
            "Never include explanations, comments, markdown, or text outside the JSON array.\n"
        )

    async def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return (response.content[0].text or "").strip()

    # ---------------------------------------------------------
    # File-edit generation
    # ---------------------------------------------------------
    async def generate_file_edits(self, prompt: str):
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                raw = await self._call_model(self.file_prompt, prompt)

                print("\n--- RAW CLAUDE OUTPUT ---")
                print(raw)
                print("--- END RAW OUTPUT ---\n")

                # 1. Try direct JSON
                try:
                    edits = json.loads(raw)
                    edits = JsonValidator.validate(edits)
                    return edits
                except Exception:
                    pass

                # 2. Extract array
                try:
                    cleaned = JsonExtractor.extract(raw)
                except Exception:
                    strict_prompt = (
                        "Return ONLY a JSON array. No prose. No markdown. No comments. "
                        "If invalid, return [].\n\nOriginal task:\n" + prompt
                    )
                    raw = await self._call_model(self.file_prompt, strict_prompt)
                    cleaned = JsonExtractor.extract(raw)

                # 3. Sanitize
                cleaned = JsonSanitizer.sanitize(cleaned)

                # 4. Parse JSON
                try:
                    edits = json.loads(cleaned)
                except Exception:
                    strict_prompt = (
                        "Return ONLY a JSON array. No prose. No markdown. No comments. "
                        "If invalid, return [].\n\nOriginal task:\n" + prompt
                    )
                    raw = await self._call_model(self.file_prompt, strict_prompt)
                    cleaned = JsonExtractor.extract(raw)
                    cleaned = JsonSanitizer.sanitize(cleaned)
                    edits = json.loads(cleaned)

                # 5. Validate + normalize
                edits = JsonValidator.validate(edits)
                return edits

            except Exception as ex:
                if attempt == max_attempts:
                    raise RuntimeError(f"OpenCode failed after {max_attempts} attempts: {ex}")
                await asyncio.sleep(1.0)

        raise RuntimeError("Unexpected failure in generate_file_edits")


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------

async def call_opencode(prompt: str, model=None):
    client = OpenCodeClient(model=model)
    return await client.generate_file_edits(prompt)


async def call_opencode_json(prompt: str, model=None):
    """
    Generic JSON helper for planning/decomposition subtasks.
    Uses hardened JSON pipeline.
    """
    client = OpenCodeClient(model=model)

    async def run(prompt_text: str) -> str:
        response = await client.client.messages.create(
            model=client.model,
            max_tokens=4096,
            system=client.json_prompt,
            messages=[{"role": "user", "content": prompt_text}],
        )
        raw = response.content[0].text
        return (raw or "").strip()

    raw = await run(prompt)

    try:
        cleaned = JsonExtractor.extract(raw)
    except Exception:
        cleaned = raw

    cleaned = JsonSanitizer.sanitize(cleaned)
    return json.loads(cleaned)
