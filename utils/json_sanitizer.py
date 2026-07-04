import json
import re

class JsonSanitizer:
    """
    Safely escapes content strings without corrupting C# code.
    """

    @staticmethod
    def sanitize(text: str) -> str:
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
