import os
import json
import sys

from openai import OpenAI
import click
from dotenv import load_dotenv

from browseruse.schema_validator import validate_instructions

# Load environment variables from .env (expects OPENAI_API_KEY)
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("Error: OPENAI_API_KEY not set in environment.", file=sys.stderr)
    sys.exit(1)

# Instantiate the OpenAI v1 client
client = OpenAI(api_key=API_KEY)

# System prompt to enforce schema-compliant JSON output with text/label locators
SYSTEM_PROMPT = """
You are BrowserUse Agent.
Translate the user's request into a JSON array strictly following the BrowserUse Instruction Schema.
For click actions:
  • Use {"action":"click","args":{"text":"<exact visible link or button text>"}}
For fill actions:
  • Use {"action":"fill","args":{"label":"<exact form field label>","text":"<input value>"}}
Only if text or label lookup is impossible, fall back to a CSS selector:
  • {"action":"click","args":{"selector":"<CSS selector>"}}
  • {"action":"fill","args":{"selector":"<CSS selector>","text":"<input value>"}}
For other actions, use:
  • navigate:      {"action":"navigate","args":{"url":"<full URL>"}}
  • wait:          {"action":"wait","args":{"timeout_ms":<integer>}}
                   or {"action":"wait","args":{"selector":"<CSS selector>","timeout_ms":<integer>"}}
  • extract_text:  {"action":"extract_text","args":{"selector":"<CSS selector>"}}
  • scroll:        {"action":"scroll","args":{"dx":<integer>,"dy":<integer>"}}
  • screenshot:    {"action":"screenshot","args":{"path":"<filename.png>"}}
                   or {"action":"screenshot","args":{"path":"<filename.png>","selector":"<CSS selector>"}}

Output ONLY the JSON array—no markdown, no explanations, no additional keys.
If you cannot fulfill the request, output an empty array: [].
"""

def generate_browser_tasks(user_request: str) -> list[dict]:
    """
    Call the OpenAI v1 API to generate browser automation instructions,
    validate them against our JSON schema, and return the list.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_request}
        ],
        temperature=0.0,
        max_tokens=500
    )

    content = resp.choices[0].message.content
    try:
        instructions = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from model response: {e}\nRaw output:\n{content}")

    validate_instructions(instructions)
    return instructions

@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("user_request", nargs=-1)
def main(user_request):
    """
    CLI entrypoint. Describe your browser automation task in plain English.
    Example:
      python ai_agent.py "Open example.com, click Sign In, fill Username with alice, Password with secret, then screenshot login.png"
    """
    query = " ".join(user_request).strip()
    if not query:
        print("[Error] No user request provided.", file=sys.stderr)
        sys.exit(1)

    try:
        tasks = generate_browser_tasks(query)
    except Exception as e:
        print(f"[Error] {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(tasks, indent=2))

if __name__ == "__main__":
    main()
