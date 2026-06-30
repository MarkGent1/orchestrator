import json

class JsonValidator:
    """
    Validates the structure of the JSON array returned by OpenCode.
    Ensures each edit contains required fields.
    """

    REQUIRED_FIELDS = {"file", "instructions", "content"}

    @staticmethod
    def validate(edits):
        if not isinstance(edits, list):
            raise ValueError("OpenCode output must be a JSON array")

        for i, edit in enumerate(edits):
            if not isinstance(edit, dict):
                raise ValueError(f"Edit #{i} is not an object")

            missing = JsonValidator.REQUIRED_FIELDS - set(edit.keys())
            if missing:
                raise ValueError(f"Edit #{i} missing fields: {missing}")

        return True
