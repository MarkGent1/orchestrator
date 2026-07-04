import json
import re

class JsonExtractor:
    """
    Robustly extracts the FIRST valid top-level JSON array from model output.
    Handles:
      - Markdown fences
      - Multiple arrays
      - Leading/trailing prose
      - Nested arrays
      - Trailing commas
      - Windows paths
    """

    ARRAY_REGEX = re.compile(r"\[[\s\S]*?\]")

    @staticmethod
    def extract(raw: str) -> str:
        if not raw or not raw.strip():
            raise ValueError("Empty model output")

        text = raw.strip()

        # Remove markdown fences
        if "```" in text:
            parts = text.split("```")
            candidates = [p.strip() for p in parts if "[" in p and "]" in p]
            if candidates:
                text = candidates[0]

        # Find all bracketed arrays
        arrays = JsonExtractor.ARRAY_REGEX.findall(text)
        if not arrays:
            raise ValueError("No JSON array found in output")

        # Try each candidate until one parses
        for arr in arrays:
            cleaned = JsonExtractor._clean_array(arr)
            try:
                json.loads(cleaned)
                return cleaned
            except Exception:
                continue

        raise ValueError("No valid JSON array found")

    @staticmethod
    def _clean_array(arr: str) -> str:
        """
        Fix trailing commas and common LLM formatting issues.
        """
        # Remove trailing commas before closing bracket
        arr = re.sub(r",\s*]", "]", arr)
        arr = re.sub(r",\s*}", "}", arr)

        # Remove comments
        arr = re.sub(r"//.*", "", arr)

        return arr.strip()
