"""Validations list page object model."""
from typing import List, Optional
from playwright.sync_api import Locator, expect
from .base_page import BasePage


class ValidationsPage(BasePage):
    """Validations list page with filtering and pagination."""

    URL_PATH = "/dashboard/validations"

    @property
    def status_filter(self) -> Locator:
        """Status filter dropdown."""
        return self.page.locator("select[name='status'], select[id*='status'], #status-filter").first

    @property
    def severity_filter(self) -> Locator:
        """Severity filter dropdown."""
        return self.page.locator("select[name='severity'], select[id*='severity'], #severity-filter").first

    @property
    def validations_table(self) -> Locator:
        """Validations table."""
        return self.page.locator("table").first

    @property
    def table_rows(self) -> Locator:
        """Table body rows."""
        return self.validations_table.locator("tbody tr")

    @property
    def table_headers(self) -> Locator:
        """Table header cells."""
        return self.validations_table.locator("thead th")

    @property
    def run_validation_button(self) -> Locator:
        """Run validation button."""
        # Button has "▶ Run Validation" text, match partial name
        btn = self.page.get_by_role("button", name="Run Validation")
        if btn.count() == 0:
            # Fallback: try to find by text content
            btn = self.page.locator("button:has-text('Run Validation')")
        return btn

    @property
    def run_validation_modal(self) -> Locator:
        """Run validation modal dialog."""
        return self.page.locator("#runValidationModal")

    @property
    def pagination(self) -> Locator:
        """Pagination controls."""
        return self.page.locator(".pagination, [class*='pag'], nav[aria-label*='pagination']").first

    @property
    def page_info(self) -> Locator:
        """Page info text (e.g., "Page 1 of 5")."""
        return self.page.locator("text=/Page \\d+/").first

    def filter_by_status(self, status: str) -> None:
        """Filter validations by status.

        Args:
            status: Status value to filter by (e.g., "pass", "fail", "approved")
        """
        self.status_filter.select_option(status)
        self.page.wait_for_load_state("networkidle")

    def filter_by_severity(self, severity: str) -> None:
        """Filter validations by severity.

        Args:
            severity: Severity value to filter by (e.g., "low", "high", "critical")
        """
        self.severity_filter.select_option(severity)
        self.page.wait_for_load_state("networkidle")

    def clear_filters(self) -> None:
        """Clear all filters."""
        try:
            self.status_filter.select_option("")
            self.severity_filter.select_option("")
            self.page.wait_for_load_state("networkidle")
        except Exception:
            pass

    def get_row_count(self) -> int:
        """Get number of validation rows."""
        return self.table_rows.count()

    def get_row_data(self, row_index: int) -> dict:
        """Get data from a specific row.

        Args:
            row_index: Row index (0-based)

        Returns:
            Dictionary with row data
        """
        row = self.table_rows.nth(row_index)
        cells = row.locator("td")
        return {
            "file_path": cells.nth(0).inner_text() if cells.count() > 0 else "",
            "status": cells.nth(1).inner_text() if cells.count() > 1 else "",
            "severity": cells.nth(2).inner_text() if cells.count() > 2 else "",
        }

    def click_view_button(self, row_index: int = 0) -> None:
        """Click view button on a row.

        Args:
            row_index: Row index (0-based)
        """
        row = self.table_rows.nth(row_index)
        view_link = row.get_by_role("link", name="View")
        if view_link.count() == 0:
            view_link = row.locator("a").last
        view_link.click()
        self.page.wait_for_load_state("networkidle")

    def open_run_validation_modal(self) -> None:
        """Open the run validation modal."""
        self.run_validation_button.click()
        self.page.wait_for_timeout(300)  # Wait for modal animation
        expect(self.run_validation_modal).to_be_visible(timeout=5000)

    def close_modal(self) -> None:
        """Close any open modal."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def go_to_page(self, page_num: int) -> None:
        """Navigate to a specific page.

        Args:
            page_num: Page number to navigate to
        """
        self.pagination.get_by_role("link", name=str(page_num)).click()
        self.page.wait_for_load_state("networkidle")

    def go_to_next_page(self) -> None:
        """Navigate to next page."""
        next_link = self.pagination.get_by_role("link", name="Next")
        if next_link.count() == 0:
            next_link = self.pagination.locator("text=>>").first
        next_link.click()
        self.page.wait_for_load_state("networkidle")

    def go_to_previous_page(self) -> None:
        """Navigate to previous page."""
        prev_link = self.pagination.get_by_role("link", name="Previous")
        if prev_link.count() == 0:
            prev_link = self.pagination.locator("text=<<").first
        prev_link.click()
        self.page.wait_for_load_state("networkidle")

    def has_pagination(self) -> bool:
        """Check if pagination controls are visible."""
        return self.pagination.is_visible()

    def get_current_page_number(self) -> Optional[int]:
        """Get current page number from pagination.

        Returns:
            Current page number or None if not determinable
        """
        try:
            active = self.pagination.locator(".active, [aria-current='page']").first
            return int(active.inner_text())
        except Exception:
            return None
