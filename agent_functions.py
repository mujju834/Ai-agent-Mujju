# agent_functions.py

FUNCTIONS = [
    {
        "name": "navigate",
        "description": "Navigate the browser to a given URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "click",
        "description": "Click an element on the page, either by visible text or a CSS selector.",
        "parameters": {
            "type": "object",
            "properties": {
                "text":     {"type": "string"},
                "selector": {"type": "string"}
            }
            # no `required` or `oneOf` here; we’ll handle missing fields in code
        }
    },
    {
        "name": "fill",
        "description": "Fill an input field, by form label or CSS selector.",
        "parameters": {
            "type": "object",
            "properties": {
                "label":    {"type": "string"},
                "selector": {"type": "string"},
                "text":     {"type": "string"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "wait",
        "description": "Wait a fixed time or for a selector to appear.",
        "parameters": {
            "type": "object",
            "properties": {
                "timeout_ms": {"type": "integer", "minimum": 0},
                "selector":   {"type": "string"}
            },
            "required": ["timeout_ms"]
        }
    },
    {
        "name": "extract_text",
        "description": "Extract visible text from a CSS selector.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot of the page or a specific selector.",
        "parameters": {
            "type": "object",
            "properties": {
                "path":     {"type": "string"},
                "selector": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "done",
        "description": "Signal that the task is complete and no further actions are needed.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
