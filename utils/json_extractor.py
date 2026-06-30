class JsonExtractor:
    """
    Extracts the FIRST valid top-level JSON array from Claude output.
    Handles multiple arrays, markdown, prose, and nested brackets.
    """

    @staticmethod
    def extract(raw: str) -> str:
        if not raw:
            raise ValueError("Empty model output")

        # Remove markdown fences
        if "```" in raw:
            parts = raw.split("```")
            for p in parts:
                if "[" in p and "]" in p:
                    raw = p.strip()
                    break

        # Find the first '['
        start = raw.find("[")
        if start == -1:
            raise ValueError("No JSON array found in output")

        # Walk forward and find the matching closing ']'
        depth = 0
        end = None

        for i in range(start, len(raw)):
            if raw[i] == "[":
                depth += 1
            elif raw[i] == "]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        if end is None:
            raise ValueError("JSON array not properly closed")

        cleaned = raw[start:end].strip()

        if not cleaned.startswith("[") or not cleaned.endswith("]"):
            raise ValueError("Extracted content is not a valid JSON array")

        return cleaned
