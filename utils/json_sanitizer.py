class JsonSanitizer:
    """
    Repairs malformed JSON produced by LLMs.
    Ensures content strings are properly escaped.
    """

    @staticmethod
    def escape_content_strings(text: str) -> str:
        """
        Rewrites `"content": "<raw>"` blocks using a proper JSON-string escape routine.
        """

        output = []
        i = 0
        n = len(text)

        while i < n:
            # Look for `"content"`
            if text.startswith('"content"', i):
                output.append('"content"')
                i += len('"content"')

                # Skip whitespace and colon
                while i < n and text[i].isspace():
                    output.append(text[i])
                    i += 1
                if i < n and text[i] == ":":
                    output.append(":")
                    i += 1
                while i < n and text[i].isspace():
                    output.append(text[i])
                    i += 1

                # Opening quote
                if i < n and text[i] == '"':
                    output.append('"')
                    i += 1
                else:
                    continue

                # Parse raw content
                content_chars = []
                while i < n:
                    ch = text[i]

                    if ch == "\\":
                        # Preserve escaped sequences
                        if i + 1 < n:
                            content_chars.append(text[i])
                            content_chars.append(text[i+1])
                            i += 2
                            continue

                    if ch == '"':
                        # End of content string
                        i += 1
                        break

                    content_chars.append(ch)
                    i += 1

                raw_content = "".join(content_chars)

                escaped = (
                    raw_content
                    .replace("\\", "\\\\")
                    .replace('"', '\\"')
                )

                output.append(escaped)
                output.append('"')
                continue

            # Normal char
            output.append(text[i])
            i += 1

        return "".join(output)

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Fixes common malformed escape sequences.
        """
        text = text.replace("\\\n", "\n")
        text = text.replace("\\\"", "\"")
        text = text.replace("\\\t", "\t")
        text = text.replace("\\\r", "\r")
        return text
