import json
import re

class JsonSanitizer:
    """
    Safely escapes content strings without corrupting C# code.
    """

    @staticmethod
    def sanitize(text: str) -> str:
        # If this already parses as valid JSON, leave it alone.
        # The regex-based "content" repair below is a best-effort
        # fallback for genuinely malformed output; it is not aware
        # of escaped quotes (e.g. C# attributes like [Route("x")]
        # or string literals in code), so running it on already-
        # valid JSON truncates those content strings and corrupts
        # otherwise-good output.
        try:
            json.loads(text)
            return text
        except Exception:
            pass

        # Fix broken escape sequences
        text = text.replace("\\\n", "\n")
        text = text.replace("\\\t", "\t")
        text = text.replace("\\\r", "\r")

        # Ensure quotes inside content are escaped
        def fix_content(match):
            raw = match.group(1)
            escaped = raw.replace("\\", "\\\\").replace('"', '\\"')
            return f'"content": "{escaped}"'

        text = re.sub(r'"content"\s*:\s*"([^"]*)"', fix_content, text)

        return text
