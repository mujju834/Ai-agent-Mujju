import pytest
from browseruse.schema_validator import validate_instructions

def test_valid_sequence():
    payload = [
        {"action": "navigate", "args": {"url": "https://example.com"}}
    ]
    validate_instructions(payload)

def test_missing_action():
    bad = [{"args": {"url": "https://foo"}}]
    with pytest.raises(ValueError) as exc:
        validate_instructions(bad)
    # Ensure the error message matches the schema validation output
    assert "'action' is a required property" in str(exc.value)
