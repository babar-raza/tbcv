"""Recommendations list page object model."""
from typing import List, Optional
from playwright.sync_api import Locator, expect
from .base_page import BasePage


class RecommendationsPage(BasePage):
    """Recommendations list page with filtering and bulk actions."""

    URL_PATH = "/dashboard/recommendations"

    @property
    def status_filter(self) -> Locator:
        """Status filter dropdown."""
        return self.page.locator("select[name='status'], select[id*='status'], #status-filter").first

    @property
    def type_filter(self) -> Locator:
        """Type filter dropdown."""
        return self.page.locator("select[name='type'], select[id*='type'], #type-filter").first

    @property
    def recommendations_table(self) -> Locator:
        """Recommendations table."""
        return self.page.locator("table").first

    @property
    def table_rows(self) -> Locator:
        """Table body rows."""
        return self.recommendations_table.locator("tbody tr")

    @property
    def table_headers(self) -> Locator:
        """Table header cells."""
        return self.recommendations_table.locator("thead th")

    @property
    def checkboxes(self) -> Locator:
        """Row selection checkboxes (in tbody)."""
        return self.recommendations_table.locator("tbody input[type='checkbox']")

    @property
    def select_all_checkbox(self) -> Locator:
        """Select all checkbox (in thead)."""
        return self.recommendations_table.locator("thead input[type='checkbox']").first

    @property
    def bulk_approve_button(self) -> Locator:
        """Bulk approve button."""
        return self.page.get_by_role("button", name="Approve")

    @property
    def bulk_reject_button(self) -> Locator:
        """Bulk reject button."""
        return self.page.get_by_role("button", name="Reject")

    @property
    def bulk_actions_container(self) -> Locator:
        """Bulk actions container."""
        return self.page.locator("[class*='bulk'], .bulk-actions, .actions").first

    @property
    def pagination(self) -> Locator:
        """Pagination controls."""
        return self.page.locator(".pagination, [class*='pag'], nav[aria-label*='pagination']").first

    def filter_by_status(self, status: str) -> None:
        """Filter by status.

        Args:
            status: Status to filter by (e.g., "pending", "accepted", "rejected")
        """
        self.status_filter.select_option(status)
        self.page.wait_for_load_state("networkidle")

    def filter_by_type(self, rec_type: str) -> None:
        """Filter by recommendation type.

        Args:
            rec_type: Type to filter by (e.g., "link_plugin", "fix_format")
        """
        self.type_filter.select_option(rec_type)
        self.page.wait_for_load_state("networkidle")

    def clear_filters(self) -> None:
        """Clear all filters."""
        try:
            self.status_filter.select_option("")
            self.type_filter.select_option("")
            self.page.wait_for_load_state("networkidle")
        except Exception:
            pass

    def get_row_count(self) -> int:
        """Get number of recommendation rows."""
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
            "title": cells.nth(1).inner_text() if cells.count() > 1 else "",
            "type": cells.nth(2).inner_text() if cells.count() > 2 else "",
            "status": cells.nth(3).inner_text() if cells.count() > 3 else "",
        }

    def select_row(self, index: int) -> None:
        """Select a row by index.

        Args:
            index: Row index (0-based)
        """
        self.checkboxes.nth(index).check()

    def deselect_row(self, index: int) -> None:
        """Deselect a row by index.

        Args:
            index: Row index (0-based)
        """
        self.checkboxes.nth(index).uncheck()

    def select_rows(self, indices: List[int]) -> None:
        """Select multiple rows.

        Args:
            indices: List of row indices to select
        """
        for i in indices:
            self.select_row(i)

    def select_all(self) -> None:
        """Select all rows using header checkbox."""
        self.select_all_checkbox.check()

    def deselect_all(self) -> None:
        """Deselect all rows using header checkbox."""
        self.select_all_checkbox.uncheck()

    def get_selected_count(self) -> int:
        """Get number of selected rows.

        Returns:
            Number of checked checkboxes
        """
        count = 0
        total = self.checkboxes.count()
        for i in range(total):
            if self.checkboxes.nth(i).is_checked():
                count += 1
        return count

    def bulk_approve(self) -> None:
        """Bulk approve selected recommendations."""
        self.bulk_approve_button.click()
        self.page.wait_for_load_state("networkidle")

    def bulk_reject(self) -> None:
        """Bulk reject selected recommendations."""
        self.bulk_reject_button.click()
        self.page.wait_for_load_state("networkidle")

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

    def go_to_page(self, page_num: int) -> None:
        """Navigate to a specific page.

        Args:
            page_num: Page number
        """
        self.pagination.get_by_role("link", name=str(page_num)).click()
        self.page.wait_for_load_state("networkidle")

    def is_bulk_approve_enabled(self) -> bool:
        """Check if bulk approve button is enabled."""
        return self.bulk_approve_button.is_enabled()

    def is_bulk_reject_enabled(self) -> bool:
        """Check if bulk reject button is enabled."""
        return self.bulk_reject_button.is_enabled()
