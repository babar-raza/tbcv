"""Dashboard home page object model."""
from typing import Optional
from playwright.sync_api import Locator, expect
from .base_page import BasePage


class DashboardHome(BasePage):
    """Dashboard home page with metrics and activity feed."""

    URL_PATH = "/dashboard/"

    @property
    def metrics_grid(self) -> Locator:
        """Metrics grid container."""
        return self.page.locator(".metrics, .stats, [class*='metric'], .card").first

    @property
    def total_validations(self) -> Locator:
        """Total validations metric."""
        return self.page.locator("text=Total").locator("..").locator("text=/\\d+/")

    @property
    def activity_feed(self) -> Locator:
        """Activity feed container."""
        return self.page.locator(".activity, [class*='activity'], [class*='feed'], .activity-feed").first

    @property
    def websocket_status(self) -> Locator:
        """WebSocket connection status indicator."""
        return self.page.locator("[class*='status'], [class*='connection'], .ws-status").first

    @property
    def recent_validations_table(self) -> Locator:
        """Recent validations table."""
        return self.page.locator("table").first

    @property
    def recent_validations_rows(self) -> Locator:
        """Rows in recent validations table."""
        return self.recent_validations_table.locator("tbody tr")

    @property
    def view_all_validations_link(self) -> Locator:
        """View all validations link."""
        return self.page.get_by_role("link", name="View All").first

    @property
    def pending_recommendations_section(self) -> Locator:
        """Pending recommendations section."""
        return self.page.locator("text=Pending").locator("..").first

    def wait_for_metrics_loaded(self, timeout: int = 5000) -> None:
        """Wait for metrics to load.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def wait_for_websocket_connected(self, timeout: int = 10000) -> None:
        """Wait for WebSocket to connect.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        try:
            self.page.wait_for_function(
                """() => {
                    const status = document.querySelector('[class*="status"], [class*="connection"], .ws-status');
                    return status && status.textContent.toLowerCase().includes('connected');
                }""",
                timeout=timeout
            )
        except Exception:
            # WebSocket may not be available in test mode
            pass

    def get_metric_value(self, metric_name: str) -> Optional[str]:
        """Get value of a specific metric.

        Args:
            metric_name: Name of the metric (e.g., "Total", "Pending")

        Returns:
            Metric value as string or None if not found
        """
        try:
            metric = self.page.locator(f"text={metric_name}").locator("..")
            value_elem = metric.locator("text=/\\d+/").first
            if value_elem.is_visible():
                return value_elem.inner_text()
        except Exception:
            pass
        return None

    def click_recent_validation(self, index: int = 0) -> None:
        """Click on a recent validation row.

        Args:
            index: Row index (0-based)
        """
        self.recent_validations_rows.nth(index).click()
        self.page.wait_for_load_state("networkidle")

    def get_activity_items(self) -> Locator:
        """Get activity feed items."""
        return self.activity_feed.locator(".activity-item, li, .item")

    def wait_for_activity_update(self, timeout: int = 10000) -> None:
        """Wait for activity feed to receive an update.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.get_activity_items().first.wait_for(state="visible", timeout=timeout)
