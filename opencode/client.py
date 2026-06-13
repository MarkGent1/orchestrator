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

    async def generate_file_edits(self, prompt: str):
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                )

                raw = (response.content[0].text or "").strip()

                print("\n--- RAW CLAUDE OUTPUT ---")
                print(raw)
                print("--- END RAW OUTPUT ---\n")

                # 1. Try direct JSON
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
                    # Regenerate with a stricter system prompt
                    strict_prompt = (
                        "Return ONLY a JSON array. No prose. No markdown. No comments. "
                        "No explanations. No multiple arrays. No text before or after. "
                        "If you cannot produce valid JSON, return [].\n\n"
                        f"Original task:\n{prompt}"
                    )

                    response = await self.client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        system=self.system_prompt,
                        messages=[{"role": "user", "content": strict_prompt}],
                    )

                    raw = (response.content[0].text or "").strip()
                    cleaned = JsonExtractor.extract(raw)

                # 3. Escape content strings
                cleaned = JsonSanitizer.escape_content_strings(cleaned)

                # 4. Sanitize broken escapes
                cleaned = JsonSanitizer.sanitize(cleaned)

                # 5. Parse JSON
                try:
                    cleaned = cleaned.lstrip()
                    edits = json.loads(cleaned)
                except Exception:
                    # Regenerate with strict prompt
                    strict_prompt = (
                        "Return ONLY a JSON array. No prose. No markdown. No comments. "
                        "No explanations. No multiple arrays. No text before or after. "
                        "If you cannot produce valid JSON, return [].\n\n"
                        f"Original task:\n{prompt}"
                    )

                    response = await self.client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        system=self.system_prompt,
                        messages=[{"role": "user", "content": strict_prompt}],
                    )

                    raw = (response.content[0].text or "").strip()
                    cleaned = JsonExtractor.extract(raw)
                    cleaned = JsonSanitizer.escape_content_strings(cleaned)
                    cleaned = JsonSanitizer.sanitize(cleaned)
                    cleaned = cleaned.lstrip()
                    edits = json.loads(cleaned)

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
# Convenience function (public API)
# ---------------------------------------------------------
async def call_opencode(prompt: str):
    client = OpenCodeClient()
    return await client.generate_file_edits(prompt)

# ---------------------------------------------------------
# Convenience: generic JSON (no file-edit validation)
# ---------------------------------------------------------
async def call_opencode_json(prompt: str):
    client = OpenCodeClient()

    async def run(prompt_text: str):
        response = await client.client.messages.create(
            model=client.model,
            max_tokens=4096,
            system=client.system_prompt,
            messages=[{"role": "user", "content": prompt_text}],
        )
        return (response.content[0].text or "").strip()

    # 1. First attempt
    raw = await run(prompt)

    # 1a. Try direct JSON
    try:
        return json.loads(raw)
    except:
        pass

    # 1b. Try array extraction
    try:
        cleaned = JsonExtractor.extract(raw)
        cleaned = JsonSanitizer.escape_content_strings(cleaned)
        cleaned = JsonSanitizer.sanitize(cleaned)
        cleaned = cleaned.lstrip()
        return json.loads(cleaned)
    except:
        pass

    # 1c. Try object extraction
    try:
        obj = extract_json_object(raw)
        obj = obj.lstrip()
        return json.loads(obj)
    except:
        pass

    # 2. Strict regeneration fallback
    strict_prompt = (
        "Return ONLY valid JSON. No prose. No markdown. No comments. "
        "No explanations. No multiple JSON values. No text before or after. "
        "If you cannot produce valid JSON, return {}.\n\n"
        f"Original task:\n{prompt}"
    )

    raw = await run(strict_prompt)

    # 2a. Try direct JSON
    try:
        return json.loads(raw)
    except:
        pass

    # 2b. Try array extraction
    try:
        cleaned = JsonExtractor.extract(raw)
        cleaned = JsonSanitizer.escape_content_strings(cleaned)
        cleaned = JsonSanitizer.sanitize(cleaned)
        cleaned = cleaned.lstrip()
        return json.loads(cleaned)
    except:
        pass

    # 2c. Try object extraction
    try:
        obj = extract_json_object(raw)
        obj = obj.lstrip()
        return json.loads(obj)
    except:
        pass

    raise RuntimeError("Unable to parse JSON from model output after strict regeneration")

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
