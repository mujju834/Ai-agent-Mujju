import json
import os
from jsonschema import validate, ValidationError, SchemaError

# Load the JSON Schema from file
_schema_path = os.path.join(os.path.dirname(__file__), "browseruse.schema.json")
with open(_schema_path, "r", encoding="utf-8") as f:
    _SCHEMA = json.load(f)


def validate_instructions(instructions):
    """
    Validate a list of browser-use instructions against the JSON schema.

    :param instructions: list of dicts, each with keys "action" and "args"
    :raises ValueError: if the instructions do not conform to the schema
    :raises RuntimeError: if the schema itself is invalid
    """
    try:
        validate(instance=instructions, schema=_SCHEMA)
    except ValidationError as ve:
        # Construct a clear error message indicating where validation failed
        location = " -> ".join(str(p) for p in ve.path) or "root"
        raise ValueError(f"Instruction validation error at '{location}': {ve.message}")
    except SchemaError as se:
        # Indicates the schema file is malformed
        raise RuntimeError(f"JSON schema error: {se.message}")


if __name__ == "__main__":
    # Quick local test
    example = [
        { "action": "navigate", "args": { "url": "https://example.com" } },
        { "action": "click",    "args": { "selector": "#start-button" } }
    ]

    try:
        validate_instructions(example)
        print("✅ Example instructions are valid.")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
