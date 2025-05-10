#!/usr/bin/env python3
import sys
import click
import asyncio
from ai_agent import run_autonomous

@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("user_goal", nargs=-1)
@click.option("--headless/--show", default=False, help="Run in headless mode")
@click.option("--slow-mo",     default=300,   help="Delay between actions (ms)")
def main(user_goal, headless, slow_mo):
    """
    Autonomous demo: Describe your goal in plain English, and watch the agent
    navigate, click, fill, wait, screenshot, etc., until completion.

    Examples:
      python demo.py "Go to mujjumujahid.com and fill in the contact form and submit it"
      python demo.py --show --slow-mo 500 "Log into Gmail and list unread subjects"
    """
    # Reconstruct the goal string (or fallback to a sensible default)
    if user_goal:
        goal = " ".join(user_goal).strip()
    else:
        goal = "Go to mujjumujahid.com and fill in the contact form and submit it twice with different names and different details for two people"

    print(f"\n🔍 USER GOAL: {goal}\n")
    print(f"▶️ Starting autonomous execution (headless={headless}, slowMo={slow_mo}ms)…\n")

    try:
        # This will print each function call as it happens
        results = asyncio.run(run_autonomous(goal, headless=headless, slow_mo=slow_mo))
    except Exception as e:
        print(f"\n[Error] {e}", file=sys.stderr)
        sys.exit(1)

    print("\n✅ ALL DONE! Collected results:")
    for r in results:
        print("  •", r)

if __name__ == "__main__":
    main()
