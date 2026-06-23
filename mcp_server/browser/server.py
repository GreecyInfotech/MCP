"""Browser Automation MCP server — navigate, interact, and extract page content."""

from __future__ import annotations

import base64
from typing import Any

from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "browser",
    instructions=(
        "Browser automation for web testing and data extraction. Navigate pages, "
        "interact with elements, capture screenshots, and extract content."
    ),
)

_browser: Any = None
_page: Any = None
_playwright: Any = None


def _ensure_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ImportError("Install browser support: pip install -e '.[mcp]'") from exc
    return sync_playwright().start()


def _launch_browser(pw: Any, settings: Any) -> Any:
    launch_kwargs: dict[str, Any] = {"headless": settings.browser_headless}
    errors: list[str] = []

    if settings.browser_executable_path:
        try:
            return pw.chromium.launch(executable_path=settings.browser_executable_path, **launch_kwargs)
        except Exception as exc:
            errors.append(f"executable_path: {exc}")

    channels = []
    if settings.browser_channel:
        channels.append(settings.browser_channel)
    for fallback in ("chrome", "msedge", "chromium"):
        if fallback not in channels:
            channels.append(fallback)

    for channel in channels:
        try:
            return pw.chromium.launch(channel=channel, **launch_kwargs)
        except Exception as exc:
            errors.append(f"{channel}: {exc}")

    hint = (
        "Could not launch a browser. Options: "
        "(1) set BROWSER_CHANNEL=chrome or msedge in .env, "
        "(2) set BROWSER_EXECUTABLE_PATH to your browser exe, "
        "(3) run: playwright install chromium"
    )
    raise RuntimeError(f"{hint}\nAttempts: {'; '.join(errors)}")


def _get_page() -> Any:
    global _browser, _page, _playwright
    if _page is None:
        settings = get_settings()
        _playwright = _ensure_playwright()
        _browser = _launch_browser(_playwright, settings)
        context = _browser.new_context()
        _page = context.new_page()
        _page.set_default_timeout(settings.browser_timeout_ms)
    return _page


@mcp.tool()
def navigate(url: str, wait_until: str = "domcontentloaded") -> str:
    """Navigate the browser to a URL."""
    try:
        page = _get_page()
        response = page.goto(url, wait_until=wait_until)
        return text_result(
            {
                "url": page.url,
                "title": page.title(),
                "status": response.status if response else None,
            }
        )
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_page_content(selector: str = "") -> str:
    """Get page text content or inner text of a CSS selector."""
    try:
        page = _get_page()
        if selector:
            element = page.query_selector(selector)
            if not element:
                return error_result(f"Selector not found: {selector}")
            content = element.inner_text()
        else:
            content = page.inner_text("body")
        return text_result({"url": page.url, "content": content[:50000]})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def click(selector: str) -> str:
    """Click an element matching a CSS selector."""
    try:
        page = _get_page()
        page.click(selector)
        return text_result({"clicked": selector, "url": page.url})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def fill(selector: str, value: str) -> str:
    """Fill an input field identified by CSS selector."""
    try:
        page = _get_page()
        page.fill(selector, value)
        return text_result({"filled": selector, "value": value})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def screenshot(full_page: bool = False, return_base64: bool = True) -> str:
    """Capture a screenshot of the current page."""
    try:
        page = _get_page()
        if return_base64:
            data = page.screenshot(full_page=full_page)
            encoded = base64.b64encode(data).decode("ascii")
            return text_result(
                {
                    "url": page.url,
                    "format": "png",
                    "base64": encoded,
                    "size_bytes": len(data),
                }
            )
        path = "screenshot.png"
        page.screenshot(path=path, full_page=full_page)
        return text_result({"url": page.url, "saved_to": path})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def evaluate_javascript(script: str) -> str:
    """Evaluate JavaScript in the browser page context."""
    try:
        page = _get_page()
        result = page.evaluate(script)
        return text_result({"url": page.url, "result": result})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_links() -> str:
    """Extract all links from the current page."""
    try:
        page = _get_page()
        links = page.eval_on_selector_all(
            "a[href]",
            "elements => elements.map(e => ({text: e.innerText.trim(), href: e.href}))",
        )
        return text_result({"url": page.url, "links": links[:200]})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def close_browser() -> str:
    """Close the browser session and release resources."""
    global _browser, _page, _playwright
    try:
        if _browser:
            _browser.close()
        if _playwright:
            _playwright.stop()
        _browser = None
        _page = None
        _playwright = None
        return text_result({"closed": True})
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
