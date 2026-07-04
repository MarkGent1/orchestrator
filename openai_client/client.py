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
    Production‑grade OpenAI → OpenCode integration using the new Responses API.
    Fully hardened against malformed JSON, markdown wrapping, unescaped quotes,
    multiline content, and partial truncation.

    Model is passed in dynamically.
    """

    def __init__(self, api_key=None, model=GPT_MINI):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model  # Dynamic model selection

        self.system_prompt = (
            "You are OpenCode. You ALWAYS return ONLY a JSON array of file edits.\n"
            "Never include explanations, comments, markdown, or text outside the JSON array.\n"
            "If no edits are needed, return [].\n"
            "Each edit must include: \"file\", \"instructions\", and \"content\".\n"
            "Your output must ALWAYS be valid JSON."
        )

    # ---------------------------------------------------------
    # Low-level model call (Responses API)
    # ---------------------------------------------------------
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
    # JSON extraction helpers
    # ---------------------------------------------------------
    def _extract_json_array(self, raw: str) -> list:
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
        except Exception:
            pass

        cleaned = JsonExtractor.extract(raw)
        cleaned = JsonSanitizer.escape_content_strings(cleaned)
        cleaned = JsonSanitizer.sanitize(cleaned)
        cleaned = cleaned.lstrip()

        data = json.loads(cleaned)
        if not isinstance(data, list):
            raise ValueError("Parsed JSON is not an array")

        return data

    def _extract_json_value(self, raw: str):
        try:
            return json.loads(raw)
        except Exception:
            pass

        try:
            cleaned = JsonExtractor.extract(raw)
            cleaned = JsonSanitizer.escape_content_strings(cleaned)
            cleaned = JsonSanitizer.sanitize(cleaned)
            cleaned = cleaned.lstrip()
            return json.loads(cleaned)
        except Exception:
            pass

        raise RuntimeError("Unable to parse JSON from model output")

    # ---------------------------------------------------------
    # File-edit generation (strict JSON array)
    # ---------------------------------------------------------
    async def generate_file_edits(self, prompt: str):
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                raw = await self._call_model(self.system_prompt, prompt)

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
                        "Return ONLY a JSON array. No prose. No markdown. No comments. "
                        "No explanations. No multiple arrays. No text before or after. "
                        "If you cannot produce valid JSON, return [].\n\n"
                        f"Original task:\n{prompt}"
                    )

                    raw = await self._call_model(self.system_prompt, strict_prompt)

                    try:
                        cleaned = JsonExtractor.extract(raw)
                    except Exception:
                        return []

                cleaned = JsonSanitizer.escape_content_strings(cleaned)
                cleaned = JsonSanitizer.sanitize(cleaned)
                cleaned = cleaned.lstrip()

                try:
                    edits = json.loads(cleaned)
                except Exception:
                    strict_prompt = (
                        "Return ONLY a JSON array. No prose. No markdown. No comments. "
                        "No explanations. No multiple arrays. No text before or after. "
                        "If you cannot produce valid JSON, return [].\n\n"
                        f"Original task:\n{prompt}"
                    )

                    raw = await self._call_model(self.system_prompt, strict_prompt)

                    try:
                        cleaned = JsonExtractor.extract(raw)
                        cleaned = JsonSanitizer.escape_content_strings(cleaned)
                        cleaned = JsonSanitizer.sanitize(cleaned)
                        cleaned = cleaned.lstrip()
                        edits = json.loads(cleaned)
                    except Exception:
                        return []

                edits = JsonValidator.validate(edits)
                return edits

            except Exception as ex:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"OpenAI failed after {max_attempts} attempts: {ex}"
                    )
                await asyncio.sleep(1.0)

        raise RuntimeError("Unexpected failure in generate_file_edits")


# ---------------------------------------------------------
# Public API: file edits (accepts model)
# ---------------------------------------------------------
async def call_openai(prompt: str, model=GPT_MINI):
    client = OpenAIClient(model=model)
    return await client.generate_file_edits(prompt)


# ---------------------------------------------------------
# Public API: generic JSON (accepts model)
# ---------------------------------------------------------
async def call_openai_json(prompt: str, model=GPT_MINI):
    client = OpenAIClient(model=model)

    def validate_subtask_shape(value):
        if not isinstance(value, list):
            raise TypeError("Expected a JSON array of subtasks")
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise TypeError(f"Subtask #{i} is not an object")
            if "title" not in item or "description" not in item:
                raise TypeError(f"Subtask #{i} missing required fields")

    async def run(prompt_text: str) -> str:
        response = await client.client.responses.create(
            model=client.model,
            input=[
                {"role": "system", "content": client.system_prompt},
                {"role": "user", "content": prompt_text},
            ],
            max_output_tokens=4096,
        )
        return (response.output_text or "").strip()

    raw = await run(prompt)

    try:
        value = client._extract_json_value(raw)
        validate_subtask_shape(value)
        return value
    except Exception:
        pass

    strict_prompt = (
        "Return ONLY a JSON array of subtasks. No prose. No markdown. No comments. "
        "No explanations. No multiple JSON values. "
        "Each item MUST contain 'title' and 'description'.\n\n"
        f"Original task:\n{prompt}"
    )

    raw = await run(strict_prompt)
    value = client._extract_json_value(raw)
    validate_subtask_shape(value)
    return value
