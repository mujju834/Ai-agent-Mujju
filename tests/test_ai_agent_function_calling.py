import json
import pytest

from ai_agent import generate_browser_tasks
from agent_functions import FUNCTIONS

class DummyFunctionCall:
    def __init__(self, name, arguments):
        self.name = name
        # Store arguments as JSON string
        self.arguments = json.dumps(arguments)

class DummyMessage:
    def __init__(self, func_name, func_args):
        self.function_call = DummyFunctionCall(func_name, func_args)

class DummyChoice:
    def __init__(self, message):
        self.message = message

class DummyResponse:
    def __init__(self, func_name, func_args):
        # Simulate an OpenAI response with a single choice
        msg = DummyMessage(func_name, func_args)
        self.choices = [DummyChoice(msg)]


def test_generate_browser_tasks_function_calling(monkeypatch):
    # Prepare a sequence of dummy responses: first navigate, then done
    responses = [
        DummyResponse("navigate", {"url": "https://example.com"}),
        DummyResponse("done", {})
    ]

    # Monkey-patch the OpenAI client's chat.completions.create to return successive dummy responses
    def fake_create(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(
        "ai_agent.client.chat.completions.create",
        fake_create
    )

    # Invoke generate_browser_tasks
    tasks = generate_browser_tasks("Go to example.com")

    # Should only return the navigate action, since done is filtered out
    assert tasks == [
        {"action": "navigate", "args": {"url": "https://example.com"}}
    ]

    # Ensure no responses left
    assert not responses