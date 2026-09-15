"""
Berilgan edupage jadval sahifasidan (guruh/o'qituvchi/xona) faqat
jadval qismining (SVG) skrinshotini olib, PNG faylga saqlaydi.

Butun brauzer sessiyasi bot ishga tushganda BIR MARTA ochiladi
(main.py -> on_startup) va yopilganda yopiladi (on_shutdown), har bir
so'rov uchun esa faqat yangi "page" ochiladi - bu tezlik uchun muhim,
chunki brauzerni har safar qayta ishga tushirish sekin bo'ladi.
"""

import uuid
from pathlib import Path

from playwright.async_api import Browser, async_playwright

from . import config

_playwright = None
_browser: Browser | None = None


async def start_browser():
    global _playwright, _browser
    if _browser is not None:
        return
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=True)


async def stop_browser():
    global _playwright, _browser
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


async def take_timetable_screenshot(url: str) -> Path:
    """Berilgan URL manzilidagi jadval qismini skrinshot qilib,
    vaqtinchalik PNG faylga saqlaydi va shu fayl yo'lini qaytaradi.
    Fayl chaqiruvchi tomonidan (Telegramga yuborilgach) o'chirilishi kerak."""
    if _browser is None:
        await start_browser()

    page = await _browser.new_page(viewport={"width": 1600, "height": 1000})
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1000)

        element = await page.query_selector("div.print-sheet svg")
        if element is None:
            element = await page.query_selector("svg")

        out_path = config.SCREENSHOT_DIR / f"{uuid.uuid4().hex}.png"

        if element is not None:
            await element.screenshot(path=str(out_path))
        else:
            # Zaxira variant: butun sahifani skrinshot qilish
            await page.screenshot(path=str(out_path), full_page=True)

        return out_path
    finally:
        await page.close()
