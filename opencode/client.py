from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import os
import json
import asyncio

from .json_extractor import JsonExtractor
from .json_sanitizer import JsonSanitizer
from .json_validator import JsonValidator

load_dotenv()


class OpenCodeClient:
    """
    Production‑grade OpenCode → Claude integration.
    Fully hardened against malformed JSON, markdown wrapping,
    unescaped quotes, multiline content, and partial truncation.
    """

    def __init__(self, api_key=None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is missing")

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-6"

        self.system_prompt = (
            "You are OpenCode. You ALWAYS return ONLY a JSON array of file edits.\n"
            "Never include explanations, comments, markdown, or text outside the JSON array.\n"
            "If no edits are needed, return an empty JSON array: [].\n"
            "Each edit must include: \"file\", \"instructions\", and \"content\".\n"
            "Your output must ALWAYS be valid JSON."
        )

    # ---------------------------------------------------------
    # Low-level model call
    # ---------------------------------------------------------
    async def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return (response.content[0].text or "").strip()

    # ---------------------------------------------------------
    # Generic JSON parsing helpers
    # ---------------------------------------------------------
    def _extract_json_array(self, raw: str) -> list:
        """
        Extracts a JSON array from raw model output using:
        1. direct json.loads
        2. array extraction
        3. sanitization
        """
        # 1. Direct JSON
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
        except Exception:
            pass

        # 2. Extract array from noisy output
        cleaned = JsonExtractor.extract(raw)
        cleaned = JsonSanitizer.escape_content_strings(cleaned)
        cleaned = JsonSanitizer.sanitize(cleaned)
        cleaned = cleaned.lstrip()

        data = json.loads(cleaned)
        if not isinstance(data, list):
            raise ValueError("Parsed JSON is not an array")

        return data

    def _extract_json_value(self, raw: str):
        """
        Extracts ANY JSON value (object or array).
        """
        # 1. Direct JSON
        try:
            return json.loads(raw)
        except Exception:
            pass

        # 2. Try array extraction
        try:
            cleaned = JsonExtractor.extract(raw)
            cleaned = JsonSanitizer.escape_content_strings(cleaned)
            cleaned = JsonSanitizer.sanitize(cleaned)
            cleaned = cleaned.lstrip()
            return json.loads(cleaned)
        except Exception:
            pass

        # 3. Try object extraction
        try:
            obj = extract_json_object(raw)
            obj = obj.lstrip()
            return json.loads(obj)
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

                print("\n--- RAW CLAUDE OUTPUT ---")
                print(raw)
                print("--- END RAW OUTPUT ---\n")

                # 1. Direct JSON
                try:
                    edits = json.loads(raw)
                    JsonValidator.validate(edits)
                    return edits
                except Exception:
                    pass

                # 2. Extract JSON array
                try:
                    cleaned = JsonExtractor.extract(raw)
                except Exception:
                    # Strict regeneration
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
                        # ⭐ FINAL FALLBACK ⭐
                        return []

                # 3. Escape content strings
                cleaned = JsonSanitizer.escape_content_strings(cleaned)

                # 4. Sanitize broken escapes
                cleaned = JsonSanitizer.sanitize(cleaned)

                # 5. Parse JSON
                try:
                    cleaned = cleaned.lstrip()
                    edits = json.loads(cleaned)
                except Exception:
                    # Strict regeneration
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
                        # ⭐ FINAL FALLBACK ⭐
                        return []

                # 6. Validate structure
                JsonValidator.validate(edits)

                return edits

            except Exception as ex:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"OpenCode failed after {max_attempts} attempts: {ex}"
                    )
                await asyncio.sleep(1.0)

        raise RuntimeError("Unexpected failure in generate_file_edits")


# ---------------------------------------------------------
# Public API: file edits
# ---------------------------------------------------------
async def call_opencode(prompt: str):
    client = OpenCodeClient()
    return await client.generate_file_edits(prompt)


# ---------------------------------------------------------
# Public API: generic JSON (task decomposition)
# ---------------------------------------------------------
async def call_opencode_json(prompt: str):
    client = OpenCodeClient()

    def validate_subtask_shape(value):
        """
        Ensures decomposition returns:
        [
          {"title": "...", "description": "..."},
          ...
        ]
        """
        if not isinstance(value, list):
            raise TypeError("Expected a JSON array of subtasks")

        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise TypeError(f"Subtask #{i} is not an object")
            if "title" not in item or "description" not in item:
                raise TypeError(f"Subtask #{i} missing required fields")

    async def run(prompt_text: str) -> str:
        response = await client.client.messages.create(
            model=client.model,
            max_tokens=4096,
            system=client.system_prompt,
            messages=[{"role": "user", "content": prompt_text}],
        )
        return (response.content[0].text or "").strip()

    # 1. First attempt
    raw = await run(prompt)

    try:
        value = client._extract_json_value(raw)
        validate_subtask_shape(value)
        return value
    except Exception:
        pass

    # 2. Strict regeneration
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


# ---------------------------------------------------------
# Object extractor
# ---------------------------------------------------------
def extract_json_object(raw: str) -> str:
    start = raw.find("{")
    if start == -1:
        raise ValueError("No JSON object found")

    depth = 0
    end = None

    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end is None:
        raise ValueError("JSON object not properly closed")

    return raw[start:end].strip()
