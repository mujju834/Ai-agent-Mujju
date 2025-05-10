import asyncio
import pytest
from browser_controller import snapshot_page, execute_instructions
from playwright.async_api import async_playwright

HTML = """
<html>
  <body>
    <a href="#foo">Foo Link</a>
    <form id="contact-form">
      <label>Name</label><input name="name"/>
      <label>Email</label><input name="email"/>
      <button type="submit">Send</button>
    </form>
    <button>ClickMe</button>
  </body>
</html>
"""

@pytest.mark.asyncio
async def test_snapshot_page_basic(tmp_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Load our HTML directly
        await page.set_content(HTML)

        summary = await snapshot_page(page)
        # Assert forms
        assert len(summary["forms"]) == 1
        form = summary["forms"][0]
        assert form["form_selector"] in ("#contact-form", ".contact-form", "form")
        assert "name" in form["fields"]
        assert "email" in form["fields"]
        assert "Send" in form["buttons"]

        # Assert links and buttons
        assert "Foo Link" in summary["links"]
        assert "ClickMe" in summary["buttons"]

        await browser.close()
