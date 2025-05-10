#!/usr/bin/env python3
import sys
import click
from ai_agent import generate_browser_tasks
from browser_controller import run

@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("user_request", nargs=-1)
def main(user_request):
    """
    Describe your task in plain English. Examples:
      python demo.py
      python demo.py "Open mujjumujahid.com, click Contact, fill Name with John Doe, Email with john.doe@example.com, Message with Hello, wait 2 seconds between actions, then screenshot form_submission.png"
    """
    if user_request:
        query = " ".join(user_request)
    else:
        query = (
            "Open mujjumujahid.com, click Contact, "
            "fill Name with Mujju millionaire, Email with mujjumillionaire@gmail.com, then click Next then"
            "Message with Mujju is a millionaire within 3 days,then click Send Message "
            "wait for 2 seconds between each action, then screenshot form_submission.png"
        )

    print(f"\n🔍 Interpreting task: {query}\n")

    try:
        tasks = generate_browser_tasks(query)
    except Exception as e:
        print(f"[Error generating tasks] {e}", file=sys.stderr)
        sys.exit(1)

    print("📝 Generated Instructions:")
    for i, step in enumerate(tasks, 1):
        print(f"  {i}. {step}")
    print()

    print("▶️ Executing in browser (headful, slowMo=300ms)…\n")
    try:
        results = run(tasks, headless=False, slow_mo=300)
    except Exception as e:
        print(f"[Error executing tasks] {e}", file=sys.stderr)
        sys.exit(1)

    print("\n✅ Execution Results:", results)

if __name__ == "__main__":
    main()
