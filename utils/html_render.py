import asyncio
import os
import tempfile
from typing import Any

from jinja2 import Template
from playwright.async_api import async_playwright

_playwright = None
_browser = None
_browser_lock = asyncio.Lock()


async def render_template_to_image(
    template_str: str,
    template_data: dict[str, Any],
    width: int = 600,
    height: int = 400,
    full_page: bool = True,
    image_type: str = "png",
    quality: int | None = None,
) -> str:
    """Render a Jinja2 HTML template to a local image file and return its path."""
    html = Template(template_str).render(**template_data)

    fd, output_path = tempfile.mkstemp(suffix=f".{image_type}")
    os.close(fd)

    browser = await _get_browser()
    page = await browser.new_page(viewport={"width": width, "height": height})
    await page.set_content(html, wait_until="networkidle")

    screenshot_kwargs: dict[str, Any] = {
        "path": output_path,
        # "full_page": full_page,
        "type": image_type,
    }
    if image_type == "jpeg" and quality is not None:
        screenshot_kwargs["quality"] = quality

    await page.locator(".card").screenshot(**screenshot_kwargs)
    await page.close()

    return output_path


async def _get_browser():
    global _playwright, _browser
    if _browser is not None:
        return _browser

    async with _browser_lock:
        if _browser is not None:
            return _browser
        _playwright = await async_playwright().start()
        _browser = await _launch_browser(_playwright)
        return _browser


async def _launch_browser(playwright):
    last_error: Exception | None = None
    for channel in ("msedge", "chrome"):
        try:
            return await playwright.chromium.launch(channel=channel, headless=True)
        except Exception as exc:
            last_error = exc
            continue

    try:
        return await playwright.chromium.launch()
    except Exception as exc:
        last_error = exc

    detail = f"{last_error}" if last_error else "unknown error"
    raise RuntimeError(
        "本地浏览器启动失败，未找到可用的 Chromium 内核。"
        "请安装 Playwright 浏览器：python -m playwright install chromium。"
        f" 详细信息: {detail}"
    )
