import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

from utils.json_extractor import JsonExtractor
from utils.json_sanitizer import JsonSanitizer
from utils.json_validator import JsonValidator
from model_constants import GPT_MINI

load_dotenv()


class OpenAIClient:
    """
    OpenAI → OpenCode client.
    Supports:
    - File edits (strict JSON array of edits)
    - Generic JSON subtasks (planning/decomposition)
    Uses hardened JSON pipeline.
    """

    def __init__(self, api_key=None, model=None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model or GPT_MINI

        # File-edit prompt
        self.file_prompt = (
            "You are OpenCode. You ALWAYS return ONLY a JSON array of file edits.\n"
            "Never include explanations, comments, markdown, or text outside the JSON array.\n"
            "If no edits are needed, return [].\n"
            "Each edit must include: \"file\", \"instructions\", and \"content\".\n"
            "Your output must ALWAYS be valid JSON."
        )

        # Generic JSON prompt
        self.json_prompt = (
            "You ALWAYS return ONLY a JSON array.\n"
            "Never include explanations, comments, markdown, or text outside the JSON array.\n"
        )

    async def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_output_tokens=4096,
        )
        raw = response.output_text
        return (raw or "").strip()

    # ---------------------------------------------------------
    # File-edit generation
    # ---------------------------------------------------------
    async def generate_file_edits(self, prompt: str):
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                raw = await self._call_model(self.file_prompt, prompt)

                print("\n--- RAW OPENAI OUTPUT ---")
                print(raw)
                print("--- END RAW OUTPUT ---\n")

                try:
                    edits = json.loads(raw)
                    edits = JsonValidator.validate(edits)
                    return edits
                except Exception:
                    pass

                try:
                    cleaned = JsonExtractor.extract(raw)
                except Exception:
                    strict_prompt = (
                        "Return ONLY a JSON array. No prose. No markdown. No comments.\n"
                        "If invalid, return [].\n\nOriginal task:\n" + prompt
                    )
                    raw = await self._call_model(self.file_prompt, strict_prompt)
                    cleaned = JsonExtractor.extract(raw)

                cleaned = JsonSanitizer.sanitize(cleaned)

                try:
                    edits = json.loads(cleaned)
                except Exception:
                    strict_prompt = (
                        "Return ONLY a JSON array. No prose. No markdown. No comments.\n"
                        "If invalid, return [].\n\nOriginal task:\n" + prompt
                    )
                    raw = await self._call_model(self.file_prompt, strict_prompt)
                    cleaned = JsonExtractor.extract(raw)
                    cleaned = JsonSanitizer.sanitize(cleaned)
                    edits = json.loads(cleaned)

                edits = JsonValidator.validate(edits)
                return edits

            except Exception as ex:
                if attempt == max_attempts:
                    raise RuntimeError(f"OpenAI failed after {max_attempts} attempts: {ex}")
                await asyncio.sleep(1.0)

        raise RuntimeError("Unexpected failure in generate_file_edits")


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------

async def call_openai(prompt: str, model=None):
    client = OpenAIClient(model=model)
    return await client.generate_file_edits(prompt)


async def call_openai_json(prompt: str, model=None):
    client = OpenAIClient(model=model)

    async def run(prompt_text: str) -> str:
        response = await client.client.responses.create(
            model=client.model,
            input=[
                {"role": "system", "content": client.json_prompt},
                {"role": "user", "content": prompt_text},
            ],
            max_output_tokens=4096,
        )
        raw = response.output_text
        return (raw or "").strip()

    raw = await run(prompt)

    try:
        cleaned = JsonExtractor.extract(raw)
    except Exception:
        cleaned = raw

    cleaned = JsonSanitizer.sanitize(cleaned)
    return json.loads(cleaned)
