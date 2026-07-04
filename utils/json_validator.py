import json

class JsonValidator:
    """
    Validates the structure of the JSON array returned by OpenCode/OpenAI.
    Ensures each edit contains required fields.
    """

    REQUIRED_FIELDS = {"file", "instructions", "content"}

    @staticmethod
    def validate(edits):
        if not isinstance(edits, list):
            raise ValueError("Model output must be a JSON array")

        for i, edit in enumerate(edits):
            if not isinstance(edit, dict):
                raise ValueError(f"Edit #{i} is not an object")

            missing = JsonValidator.REQUIRED_FIELDS - set(edit.keys())
            if missing:
                raise ValueError(f"Edit #{i} missing fields: {missing}")

            # Extra safety: ensure fields are strings
            for field in JsonValidator.REQUIRED_FIELDS:
                if not isinstance(edit[field], str):
                    raise ValueError(f"Edit #{i} field '{field}' must be a string")

        return True
