class JsonExtractor:
    """
    Extracts the FIRST valid top-level JSON array from model output.
    Handles markdown fences, prose, nested arrays, and noisy output.
    """

    @staticmethod
    def extract(raw: str) -> str:
        if not raw:
            raise ValueError("Empty model output")

        text = raw.strip()

        # Remove markdown fences (Claude sometimes wraps output)
        if "```" in text:
            parts = text.split("```")
            for p in parts:
                if "[" in p and "]" in p:
                    text = p.strip()
                    break

        # Find first '['
        start = text.find("[")
        if start == -1:
            raise ValueError("No JSON array found in output")

        depth = 0
        end = None

        for i in range(start, len(text)):
            ch = text[i]

            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        if end is None:
            raise ValueError("JSON array not properly closed")

        cleaned = text[start:end].strip()

        if not cleaned.startswith("[") or not cleaned.endswith("]"):
            raise ValueError("Extracted content is not a valid JSON array")

        return cleaned
