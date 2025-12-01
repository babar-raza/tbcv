"""Workflows list page object model."""
from typing import Optional
from playwright.sync_api import Locator, expect
from .base_page import BasePage


class WorkflowsPage(BasePage):
    """Workflows list page with state filtering."""

    URL_PATH = "/dashboard/workflows"

    @property
    def state_filter(self) -> Locator:
        """State filter dropdown."""
        return self.page.locator("select[name='state'], select[id*='state'], #state-filter").first

    @property
    def workflows_table(self) -> Locator:
        """Workflows table."""
        return self.page.locator("table").first

    @property
    def table_rows(self) -> Locator:
        """Table body rows."""
        return self.workflows_table.locator("tbody tr")

    @property
    def table_headers(self) -> Locator:
        """Table header cells."""
        return self.workflows_table.locator("thead th")

    @property
    def run_workflow_button(self) -> Locator:
        """Run workflow button."""
        # Button has "▶ Run Workflow" text, match partial name
        btn = self.page.get_by_role("button", name="Run Workflow")
        if btn.count() == 0:
            # Fallback: try to find by text content
            btn = self.page.locator("button:has-text('Run Workflow')")
        return btn

    @property
    def run_workflow_modal(self) -> Locator:
        """Run workflow modal."""
        return self.page.locator("#runWorkflowModal")

    @property
    def active_runs_section(self) -> Locator:
        """Active runs section."""
        return self.page.locator("[class*='active'], .active-runs, .running").first

    @property
    def pagination(self) -> Locator:
        """Pagination controls."""
        return self.page.locator(".pagination, [class*='pag'], nav[aria-label*='pagination']").first

    def filter_by_state(self, state: str) -> None:
        """Filter by workflow state.

        Args:
            state: State to filter by (e.g., "pending", "running", "completed")
        """
        self.state_filter.select_option(state)
        self.page.wait_for_load_state("networkidle")

    def clear_filter(self) -> None:
        """Clear state filter."""
        try:
            self.state_filter.select_option("")
            self.page.wait_for_load_state("networkidle")
        except Exception:
            pass

    def get_row_count(self) -> int:
        """Get number of workflow rows."""
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
            "id": cells.nth(0).inner_text() if cells.count() > 0 else "",
            "type": cells.nth(1).inner_text() if cells.count() > 1 else "",
            "state": cells.nth(2).inner_text() if cells.count() > 2 else "",
            "progress": cells.nth(3).inner_text() if cells.count() > 3 else "",
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

    def open_run_workflow_modal(self) -> None:
        """Open run workflow modal."""
        self.run_workflow_button.click()
        self.page.wait_for_timeout(300)  # Wait for modal animation
        expect(self.run_workflow_modal).to_be_visible(timeout=5000)

    def close_modal(self) -> None:
        """Close any open modal."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def has_active_runs(self) -> bool:
        """Check if there are active workflow runs.

        Returns:
            True if active runs section is visible and has content
        """
        if not self.active_runs_section.is_visible():
            return False
        return self.active_runs_section.locator("*").count() > 0

    def go_to_page(self, page_num: int) -> None:
        """Navigate to a specific page.

        Args:
            page_num: Page number
        """
        self.pagination.get_by_role("link", name=str(page_num)).click()
        self.page.wait_for_load_state("networkidle")

    def get_workflow_states(self) -> list:
        """Get list of all workflow states in the table.

        Returns:
            List of state strings
        """
        states = []
        count = self.table_rows.count()
        for i in range(count):
            data = self.get_row_data(i)
            if data.get("state"):
                states.append(data["state"].lower())
        return states
