"""Base page class for all Page Object Models."""
from typing import Optional
from playwright.sync_api import Page, Locator, expect


class BasePage:
    """Base class with common page functionality."""

    URL_PATH: str = "/"

    def __init__(self, page: Page, base_url: str):
        """Initialize the page object.

        Args:
            page: Playwright page instance
            base_url: Base URL for the application (e.g., http://localhost:8585)
        """
        self.page = page
        self.base_url = base_url.rstrip("/")

    def navigate(self) -> "BasePage":
        """Navigate to this page."""
        self.page.goto(f"{self.base_url}{self.URL_PATH}")
        self.page.wait_for_load_state("networkidle")
        return self

    @property
    def header(self) -> Locator:
        """Header element."""
        return self.page.locator("header")

    @property
    def nav_links(self) -> Locator:
        """Navigation links in header."""
        return self.header.get_by_role("link")

    def click_nav_link(self, name: str) -> None:
        """Click a navigation link by name.

        Args:
            name: Text of the navigation link to click
        """
        self.page.get_by_role("link", name=name).click()
        self.page.wait_for_load_state("networkidle")

    def get_page_title(self) -> str:
        """Get the page title."""
        return self.page.title()

    def has_text(self, text: str) -> bool:
        """Check if page contains text.

        Args:
            text: Text to search for

        Returns:
            True if text is visible on page
        """
        return self.page.get_by_text(text).first.is_visible()

    def wait_for_text(self, text: str, timeout: int = 5000) -> None:
        """Wait for text to appear on page.

        Args:
            text: Text to wait for
            timeout: Maximum wait time in milliseconds
        """
        self.page.get_by_text(text).first.wait_for(state="visible", timeout=timeout)

    def get_toast_message(self) -> Optional[str]:
        """Get toast notification message if present.

        Returns:
            Toast message text or None if no toast visible
        """
        toast = self.page.locator(".toast, .alert, [role='alert']").first
        if toast.is_visible():
            return toast.inner_text()
        return None

    def wait_for_navigation(self, timeout: int = 5000) -> None:
        """Wait for navigation to complete.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def get_current_url(self) -> str:
        """Get current page URL."""
        return self.page.url

    def go_back(self) -> None:
        """Navigate back in browser history."""
        self.page.go_back()
        self.page.wait_for_load_state("networkidle")

    def refresh(self) -> None:
        """Refresh the current page."""
        self.page.reload()
        self.page.wait_for_load_state("networkidle")
