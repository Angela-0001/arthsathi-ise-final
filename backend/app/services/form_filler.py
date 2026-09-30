"""
Form automation using Playwright.
Falls back gracefully if Playwright is not installed.
"""
from app.models.user import User


async def prefill_form(url: str, user: User) -> dict:
    profile = {
        "name": getattr(user, "full_name", ""),
        "phone": user.phone or "",
        "state": user.state or "",
        "occupation": user.occupation or "",
        "income": str(user.monthly_income or ""),
        "age": str(user.age or ""),
    }

    try:
        from playwright.async_api import async_playwright

        filled_fields = {}
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000)

            field_map = {
                "input[name*='name']": profile["name"],
                "input[name*='phone'], input[name*='mobile']": profile["phone"],
                "input[name*='income']": profile["income"],
                "input[name*='age']": profile["age"],
            }

            for selector, value in field_map.items():
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0 and value:
                        await element.fill(value)
                        filled_fields[selector] = value
                except Exception:
                    pass

            await browser.close()
        return filled_fields

    except ImportError:
        print("[form_filler] Playwright not installed. Run: pip install playwright && playwright install chromium")
        return {"note": "Form auto-fill not available. Install Playwright to enable.", "profile": profile}
