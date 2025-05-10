import asyncio
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError
)

async def execute_instructions(
    instructions: list[dict],
    headless: bool = False,
    slow_mo: int = 250
):
    """
    Run instructions via Playwright in a headful browser (by default).
    For click:
      - First tries content-based: get_by_text or locator(filter has_text)
      - If that fails, tries the CSS selector.
    For fill:
      - First tries label-based: get_by_label
      - If that fails, tries the CSS selector.
    """
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo)
        page    = await browser.new_page()
        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)

        for instr in instructions:
            action = instr["action"]
            args   = instr["args"]

            if action == "navigate":
                await page.goto(args["url"])

            elif action == "wait":
                if "selector" in args:
                    await page.wait_for_selector(args["selector"], timeout=args["timeout_ms"])
                else:
                    await asyncio.sleep(args["timeout_ms"] / 1000)

            elif action == "click":
                clicked = False

                # 1️⃣ If user gave us text, try clicking by the visible text first
                if "text" in args:
                    try:
                        # get_by_text(...).first picks the first matching element
                        btn = page.get_by_text(args["text"], exact=True).first
                        await btn.wait_for(state="visible", timeout=5000)
                        await btn.click()
                        clicked = True
                    except PlaywrightTimeoutError:
                        print(f"[Info] Text-based click failed for '{args['text']}'")

                # 2️⃣ If still not clicked and user provided a selector, use that
                if not clicked and "selector" in args:
                    sel = args["selector"]
                    try:
                        await page.wait_for_selector(sel, timeout=5000)
                        el = await page.query_selector(sel)
                        await el.scroll_into_view_if_needed()
                        await el.click()
                        clicked = True
                    except PlaywrightTimeoutError:
                        print(f"[Warning] CSS selector click failed: {sel}")

                if not clicked:
                    print(f"[Error] Cannot click element for args: {args}")

            elif action == "fill":
                filled = False

                # 1️⃣ If user gave us a label, try filling by form label first
                if "label" in args:
                    try:
                        locator = page.get_by_label(args["label"])
                        await locator.wait_for(state="visible", timeout=5000)
                        await locator.fill(args["text"])
                        filled = True
                    except PlaywrightTimeoutError:
                        print(f"[Info] Label-based fill failed for '{args['label']}'")

                # 2️⃣ If still not filled and user provided a selector, use that
                if not filled and "selector" in args:
                    sel = args["selector"]
                    try:
                        await page.wait_for_selector(sel, timeout=5000)
                        el = await page.query_selector(sel)
                        await el.scroll_into_view_if_needed()
                        await el.fill(args["text"])
                        filled = True
                    except PlaywrightTimeoutError:
                        print(f"[Warning] CSS selector fill failed: {sel}")

                if not filled:
                    print(f"[Error] Cannot fill element for args: {args}")

            elif action == "scroll":
                await page.evaluate(f"window.scrollBy({args['dx']}, {args['dy']})")

            elif action == "screenshot":
                path = args["path"]
                if "selector" in args:
                    try:
                        el = await page.wait_for_selector(args["selector"], timeout=5000)
                        await el.screenshot(path=path)
                    except PlaywrightTimeoutError:
                        print(f"[Warning] Screenshot selector failed: {args['selector']}")
                else:
                    await page.screenshot(path=path, full_page=True)
                results.append({"screenshot": path})

            elif action == "extract_text":
                sel = args["selector"]
                try:
                    await page.wait_for_selector(sel, timeout=5000)
                    text = await page.text_content(sel)
                    results.append({"extracted_text": text})
                except PlaywrightTimeoutError:
                    print(f"[Warning] extract_text selector failed: {sel}")

            else:
                print(f"[Error] Unsupported action: {action}")

        # pause so you can see the final state
        await asyncio.sleep(2)
        await browser.close()

    return results

def run(instructions: list[dict], headless: bool = False, slow_mo: int = 250):
    """Sync wrapper."""
    return asyncio.run(execute_instructions(instructions, headless, slow_mo))
