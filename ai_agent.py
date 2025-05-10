#!/usr/bin/env python3
import os
import sys
import json
import asyncio

import click
from dotenv import load_dotenv
from openai import OpenAI
from playwright.async_api import async_playwright

from agent_functions import FUNCTIONS
from browseruse.schema_validator import validate_instructions
from browser_controller import snapshot_page, execute_single

# Load API key
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("Error: OPENAI_API_KEY not set.", file=sys.stderr)
    sys.exit(1)

# Instantiate client
client = OpenAI(api_key=API_KEY)

# Autonomous system prompt
AUTONOMOUS_SYSTEM_PROMPT = """
You are a self-driving browser agent. Each turn:
1. I will give you a summary of the current page (forms, fields, links, buttons).
2. You know my high-level goal.
3. You must choose exactly ONE function to call next, from FUNCTIONS.
4. Return a JSON object {"name": "...", "arguments": { ... }} and nothing else.

Functions:
- navigate(url)
- click(text) or click(selector)
- fill(label,text) or fill(selector,text)
- wait(timeout_ms) or wait(selector,timeout_ms)
- extract_text(selector)
- scroll(dx,dy)
- screenshot(path) or screenshot(path,selector)
- done() → signals completion

Do NOT output any explanations or markdown.
"""

async def run_autonomous(
    user_goal: str,
    headless: bool = False,
    slow_mo: int = 250
) -> list[dict]:
    """
    Main control loop: observe → reason → act → repeat, until done.
    Returns list of results from extract_text/screenshot.
    """
    messages = [
        {"role": "system", "content": AUTONOMOUS_SYSTEM_PROMPT}
    ]
    results = []

    # Launch browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo)
        page = await browser.new_page()

        done = False
        while not done:
            # 1️⃣ Observe: snapshot the page
            dom_summary = await snapshot_page(page)
            messages.append({
                "role": "assistant",
                "content": json.dumps(dom_summary)
            })
            # 2️⃣ Reason: ask LLM what to do next
            messages.append({"role": "user", "content": user_goal})

            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                functions=FUNCTIONS,
                function_call="auto",
                temperature=0.0,
                max_tokens=200
            )
            msg = resp.choices[0].message
            if not msg.function_call:
                raise RuntimeError("Agent did not call a function")

            name = msg.function_call.name
            args = json.loads(msg.function_call.arguments)

            # 3️⃣ If done, break
            if name == "done":
                done = True
                continue

            # 4️⃣ Otherwise, execute the single action
            instr = {"action": name, "args": args}
            # Validate step
            validate_instructions([instr])
            # Execute step
            try:
                step_result = await execute_single(page, instr)
                if step_result is not None:
                    results.append(step_result)
            except Exception as e:
                print(f"[Error executing step {instr}]: {e}", file=sys.stderr)

            # 5️⃣ Feed the function call back into the conversation
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": name,
                    "arguments": msg.function_call.arguments
                }
            })

        # Close browser
        await browser.close()

    return results

@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("user_goal", nargs=-1)
@click.option("--headless/--show", default=False, help="Run in headless mode")
@click.option("--slow-mo",     default=250,   help="Delay between actions (ms)")
def main(user_goal, headless, slow_mo):
    """
    Autonomous browser agent. Describe your goal in plain English:

      python ai_agent.py "Go to mujjumujahid.com and fill out the contact form"
    """
    goal = " ".join(user_goal).strip()
    if not goal:
        print("[Error] No goal provided.", file=sys.stderr)
        sys.exit(1)

    results = asyncio.run(run_autonomous(goal, headless, slow_mo))
    print("✅ Final results:", results)

if __name__ == "__main__":
    main()
