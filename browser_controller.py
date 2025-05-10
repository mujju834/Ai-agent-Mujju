import asyncio
import json
from typing import Any, Dict, Optional
from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError
)

async def snapshot_page(page: Page) -> Dict[str, Any]:
    """
    Return a summary of the current page's interactive elements:
      - forms: each with a selector, list of field names, and button texts
      - links: visible link texts
      - buttons: visible button texts
    """
    summary: Dict[str, Any] = {"forms": [], "links": [], "buttons": []}

    # Forms & their fields/buttons
    for form in await page.query_selector_all("form"):
        form_id = await form.get_attribute("id")
        form_cls = await form.get_attribute("class")
        selector = (
            f"#{form_id}"
            if form_id else
            (f".{form_cls.split()[0]}" if form_cls else "form")
        )
        fields = []
        for inp in await form.query_selector_all("input,textarea,select"):
            name = (
                await inp.get_attribute("name")
                or await inp.get_attribute("id")
                or ""
            )
            fields.append(name)
        btns = await form.query_selector_all("button, input[type=submit]")
        buttons = [await b.text_content() for b in btns]
        summary["forms"].append({
            "form_selector": selector,
            "fields": fields,
            "buttons": buttons
        })

    # Top-level links
    links = await page.query_selector_all("a")
    summary["links"] = [await a.text_content() for a in links]

    # Top-level buttons (outside forms)
    buttons = await page.query_selector_all("button")
    summary["buttons"] = [await b.text_content() for b in buttons]

    return summary

async def execute_single(page: Page, instr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Execute exactly one instruction on the given Playwright page.
    Returns a result dict for screenshot/extract_text, or None otherwise.
    """
    action = instr["action"]
    args   = instr["args"]

    if action == "navigate":
        await page.goto(args["url"])
        return None

    if action == "wait":
        if "selector" in args:
            await page.wait_for_selector(args["selector"], timeout=args["timeout_ms"])
        else:
            await asyncio.sleep(args["timeout_ms"] / 1000)
        return None

    if action == "click":
        clicked = False
        text = args.get("text")
        selector = args.get("selector")

        # 1️⃣ text-first attempts
        if text:
            # try exact text
            try:
                btn = page.get_by_text(text, exact=True).first
                await btn.wait_for(state="visible", timeout=5000)
                await btn.click()
                clicked = True
            except PlaywrightTimeoutError:
                pass
            # try button role
            if not clicked:
                try:
                    btn = page.get_by_role("button", name=text)
                    await btn.click()
                    clicked = True
                except Exception:
                    pass
            # try link role
            if not clicked:
                try:
                    link = page.get_by_role("link", name=text)
                    await link.click()
                    clicked = True
                except Exception:
                    pass
            # try fallback locator
            if not clicked:
                try:
                    loc = page.locator(f"button:has-text(\"{text}\")").first
                    await loc.click()
                    clicked = True
                except Exception:
                    pass

        # 2️⃣ selector-fallback
        if not clicked and selector:
            try:
                el = await page.wait_for_selector(selector, timeout=5000)
                await el.scroll_into_view_if_needed()
                await el.click()
                clicked = True
            except PlaywrightTimeoutError:
                pass

        if not clicked:
            print(f"[Error] Cannot click element for args: {args}")
        return None

    if action == "fill":
        filled = False
        text = args.get("text")
        label = args.get("label")
        selector = args.get("selector")

        # 1️⃣ label-first
        if label:
            try:
                fld = page.get_by_label(label)
                await fld.wait_for(state="visible", timeout=5000)
                await fld.fill(text)
                filled = True
            except PlaywrightTimeoutError:
                pass

        # 2️⃣ selector-fallback
        if not filled and selector:
            try:
                fld = await page.wait_for_selector(selector, timeout=5000)
                await fld.scroll_into_view_if_needed()
                await fld.fill(text)
                filled = True
            except PlaywrightTimeoutError:
                pass

        # 3️⃣ name-attribute fallback
        if not filled and label:
            sel = f"[name='{label}']"
            try:
                fld = await page.wait_for_selector(sel, timeout=5000)
                await fld.fill(text)
                filled = True
            except PlaywrightTimeoutError:
                pass

        if not filled:
            print(f"[Error] Cannot fill element for args: {args}")
        return None

    if action == "scroll":
        await page.evaluate(f"window.scrollBy({args['dx']}, {args['dy']})")
        return None

    if action == "screenshot":
        path = args["path"]
        if "selector" in args:
            try:
                el = await page.wait_for_selector(args["selector"], timeout=5000)
                await el.screenshot(path=path)
            except PlaywrightTimeoutError:
                print(f"[Warning] Screenshot selector failed: {args['selector']}")
        else:
            await page.screenshot(path=path, full_page=True)
        return {"screenshot": path}

    if action == "extract_text":
        sel = args["selector"]
        try:
            el = await page.wait_for_selector(sel, timeout=5000)
            text = await el.text_content()
            return {"extracted_text": text}
        except PlaywrightTimeoutError:
            print(f"[Warning] extract_text selector failed: {sel}")
        return None

    print(f"[Error] Unsupported action: {action}")
    return None

async def execute_instructions(
    instructions: list[Dict[str, Any]],
    headless: bool = False,
    slow_mo: int = 250
) -> list[Dict[str, Any]]:
    """
    Run a sequence of instructions via Playwright.
    Returns a list of result dicts for screenshot/extract_text.
    """
    results: list[Dict[str, Any]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo)
        page    = await browser.new_page()
        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)

        for instr in instructions:
            try:
                res = await execute_single(page, instr)
                if res is not None:
                    results.append(res)
            except Exception as e:
                print(f"[Error] executing {instr}: {e}")

        # Pause so you can observe the final state
        await asyncio.sleep(2)
        await browser.close()

    return results

def run(
    instructions: list[Dict[str, Any]],
    headless: bool = False,
    slow_mo: int = 250
) -> list[Dict[str, Any]]:
    """Synchronous wrapper around the async executor."""
    return asyncio.run(execute_instructions(instructions, headless, slow_mo))

__all__ = ["snapshot_page", "execute_single", "execute_instructions", "run"]
