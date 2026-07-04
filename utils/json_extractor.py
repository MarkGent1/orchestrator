import json
import re

class JsonExtractor:
    """
    Hardened JSON array extractor for LLM output.
    Handles:
      - Multiple markdown fences
      - Multiple JSON blocks
      - Language tags (```json)
      - Leading/trailing prose
      - Multiple arrays
      - Nested arrays
      - Trailing commas
      - Comments
      - Escaped content
    """

    @staticmethod
    def extract(raw: str) -> str:
        if not raw or not raw.strip():
            raise ValueError("Empty model output")

        text = raw.strip()

        # ---------------------------------------------------------
        # Split on ALL markdown fences
        # ---------------------------------------------------------
        blocks = []
        if "```" in text:
            parts = text.split("```")
            for p in parts:
                p = p.strip()

                # Remove language tag like "json"
                if p.startswith("json"):
                    p = p[4:].strip()

                if "[" in p and "]" in p:
                    blocks.append(p)
        else:
            blocks = [text]

        # ---------------------------------------------------------
        # Extract arrays from ALL blocks
        # ---------------------------------------------------------
        arrays = []
        for block in blocks:
            arrays.extend(JsonExtractor._find_json_arrays(block))

        if not arrays:
            raise ValueError("No JSON array found in output")

        # ---------------------------------------------------------
        # Try each candidate until one parses
        # ---------------------------------------------------------
        for arr in arrays:
            # Fast path: if the extracted array is already valid
            # JSON, use it untouched. _clean_array below rewrites
            # the text (stripping "//" comments, trailing commas,
            # etc.) and, even when string-aware, is a best-effort
            # repair -- never apply it to output that already parses.
            try:
                json.loads(arr)
                return arr
            except Exception:
                pass

            cleaned = JsonExtractor._clean_array(arr)

            try:
                json.loads(cleaned)
                return cleaned
            except Exception:
                continue

        raise ValueError("No valid JSON array found")

    @staticmethod
    def _find_json_arrays(text: str):
        r"""
        Scan for top-level, balanced [...] substrings using a
        depth counter that is aware of JSON string literals.

        A naive regex like r"\[[\s\S]*?\]" breaks as soon as the
        payload contains bracket characters inside a JSON string
        value -- e.g. generated C# code with attributes such as
        [ApiController], [HttpGet], [Route("users")]. Those look
        like array boundaries to a regex but are just text inside
        a "content" field. This scanner tracks whether it is
        currently inside a quoted string (respecting escapes) and
        only counts [ / ] toward nesting depth when outside one,
        so it finds the real, full extent of each top-level array.
        """
        results = []
        i = 0
        n = len(text)

        while i < n:
            if text[i] != "[":
                i += 1
                continue

            start = i
            depth = 0
            in_string = False
            escape = False
            j = i

            while j < n:
                ch = text[j]

                if in_string:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == '"':
                        in_string = False
                else:
                    if ch == '"':
                        in_string = True
                    elif ch == "[":
                        depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0:
                            results.append(text[start:j + 1])
                            break

                j += 1

            # Resume scanning right after this array (or after the
            # unmatched '[' if it never closed properly).
            i = j + 1

        return results

    @staticmethod
    def _split_json_segments(text: str):
        """
        Split text into (is_string, segment) chunks, where string
        segments are complete JSON string literals (quotes included)
        and non-string segments are everything structural in between
        (brackets, commas, whitespace, etc).
        """
        segments = []
        current = []
        in_string = False
        escape = False

        for ch in text:
            if not in_string:
                if ch == '"':
                    if current:
                        segments.append((False, "".join(current)))
                    current = [ch]
                    in_string = True
                else:
                    current.append(ch)
            else:
                current.append(ch)
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                    segments.append((True, "".join(current)))
                    current = []

        if current:
            segments.append((in_string, "".join(current)))

        return segments

    @staticmethod
    def _clean_array(arr: str) -> str:
        """
        Fix trailing commas, comments, and common LLM formatting
        issues -- but ONLY in the structural (non-string) parts of
        the JSON. Code inside "content" string values routinely
        contains "//" comments, "/* */" comments, and comma-brace
        sequences that look like JSON mistakes but are perfectly
        valid C#/etc source text; those must be left untouched.
        """
        cleaned_parts = []
        for is_string, seg in JsonExtractor._split_json_segments(arr):
            if is_string:
                cleaned_parts.append(seg)
            else:
                seg = re.sub(r"//.*", "", seg)
                seg = re.sub(r"/\*[\s\S]*?\*/", "", seg)
                # Trailing commas before a closing bracket -- applied
                # per-segment (not on the rejoined text) so this can
                # never reach into a string literal's content.
                seg = re.sub(r",\s*]", "]", seg)
                seg = re.sub(r",\s*}", "}", seg)
                cleaned_parts.append(seg)

        text = "".join(cleaned_parts)
        return text.strip()
