import json

class JsonValidator:
    """
    Validates JSON array of edits.
    Allows extra fields.
    Allows nulls/booleans/numbers for content (converted to string).
    """

    REQUIRED = {"file", "instructions", "content"}

    @staticmethod
    def validate(edits):
        if not isinstance(edits, list):
            raise ValueError("Model output must be a JSON array")

        validated = []

        for i, edit in enumerate(edits):
            if not isinstance(edit, dict):
                raise ValueError(f"Edit #{i} is not an object")

            missing = JsonValidator.REQUIRED - set(edit.keys())
            if missing:
                raise ValueError(f"Edit #{i} missing fields: {missing}")

            # Normalize fields to strings
            fixed = {}
            for key in edit:
                val = edit[key]

                if val is None:
                    val = ""
                elif isinstance(val, (bool, int, float)):
                    val = str(val)
                elif not isinstance(val, str):
                    val = json.dumps(val)

                fixed[key] = val

            validated.append(fixed)

        return validated
