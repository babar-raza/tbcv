"""Workflow detail page object model."""
from typing import Optional
from playwright.sync_api import Locator, expect
from .base_page import BasePage


class WorkflowDetailPage(BasePage):
    """Workflow detail page with real-time progress."""

    URL_PATH = "/dashboard/workflows/{id}"

    def navigate_to(self, workflow_id: int) -> "WorkflowDetailPage":
        """Navigate to a specific workflow.

        Args:
            workflow_id: ID of the workflow to view

        Returns:
            Self for method chaining
        """
        self.page.goto(f"{self.base_url}/dashboard/workflows/{workflow_id}")
        self.page.wait_for_load_state("networkidle")
        return self

    @property
    def status_badge(self) -> Locator:
        """Status badge."""
        return self.page.locator(".badge, .status, [class*='badge'], [class*='status']").first

    @property
    def workflow_type(self) -> Locator:
        """Workflow type display."""
        return self.page.locator("[class*='type'], .type").first

    @property
    def progress_bar(self) -> Locator:
        """Progress bar element."""
        return self.page.locator("[role='progressbar'], .progress, [class*='progress'], progress").first

    @property
    def progress_text(self) -> Locator:
        """Progress percentage text."""
        return self.page.locator("[class*='progress'] text, .progress-text, text=/\\d+%/").first

    @property
    def websocket_status(self) -> Locator:
        """WebSocket connection status."""
        return self.page.locator("[class*='connection'], [class*='ws-status'], .connection-status").first

    @property
    def stats_section(self) -> Locator:
        """Workflow stats section."""
        return self.page.locator("[class*='stats'], .stats, .workflow-stats").first

    @property
    def validations_table(self) -> Locator:
        """Included validations table."""
        return self.page.locator("table").first

    @property
    def validation_rows(self) -> Locator:
        """Validation table rows."""
        return self.validations_table.locator("tbody tr")

    @property
    def pause_button(self) -> Locator:
        """Pause workflow button."""
        return self.page.get_by_role("button", name="Pause")

    @property
    def resume_button(self) -> Locator:
        """Resume workflow button."""
        return self.page.get_by_role("button", name="Resume")

    @property
    def cancel_button(self) -> Locator:
        """Cancel workflow button."""
        return self.page.get_by_role("button", name="Cancel")

    @property
    def back_link(self) -> Locator:
        """Back to list link."""
        return self.page.get_by_role("link", name="Back")

    @property
    def error_message(self) -> Locator:
        """Error message display (for failed workflows)."""
        return self.page.locator("[class*='error'], .error, .error-message").first

    def get_progress_value(self) -> int:
        """Get current progress percentage.

        Returns:
            Progress value as integer (0-100)
        """
        # Try aria-valuenow first
        aria_value = self.progress_bar.get_attribute("aria-valuenow")
        if aria_value:
            try:
                return int(float(aria_value))
            except ValueError:
                pass

        # Try value attribute (for <progress> element)
        value = self.progress_bar.get_attribute("value")
        if value:
            try:
                return int(float(value))
            except ValueError:
                pass

        # Try parsing from text
        try:
            text = self.progress_text.inner_text()
            import re
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
        except Exception:
            pass

        return 0

    def get_status(self) -> str:
        """Get current workflow status.

        Returns:
            Status text
        """
        return self.status_badge.inner_text().strip().lower()

    def get_validation_count(self) -> int:
        """Get number of included validations.

        Returns:
            Number of validation rows
        """
        return self.validation_rows.count()

    def wait_for_progress_change(self, initial_value: int, timeout: int = 15000) -> None:
        """Wait for progress to change from initial value.

        Args:
            initial_value: Starting progress value
            timeout: Maximum wait time in milliseconds
        """
        self.page.wait_for_function(
            f"""() => {{
                const bar = document.querySelector('[role="progressbar"], .progress, progress');
                if (!bar) return false;
                const current = bar.getAttribute('aria-valuenow') || bar.getAttribute('value') || '0';
                return parseInt(current) !== {initial_value};
            }}""",
            timeout=timeout
        )

    def wait_for_completion(self, timeout: int = 60000) -> None:
        """Wait for workflow to complete.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.page.wait_for_function(
            """() => {
                const status = document.querySelector('.badge, .status, [class*="badge"]');
                if (!status) return false;
                const text = status.textContent.toLowerCase();
                return text.includes('completed') || text.includes('failed') || text.includes('cancelled');
            }""",
            timeout=timeout
        )

    def wait_for_websocket_connected(self, timeout: int = 10000) -> None:
        """Wait for WebSocket to connect.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        try:
            self.page.wait_for_function(
                """() => {
                    const status = document.querySelector('[class*="connection"], [class*="ws-status"]');
                    return status && status.textContent.toLowerCase().includes('connected');
                }""",
                timeout=timeout
            )
        except Exception:
            # WebSocket may not be available
            pass

    def pause_workflow(self) -> None:
        """Pause the workflow."""
        self.pause_button.click()
        self.page.wait_for_load_state("networkidle")

    def resume_workflow(self) -> None:
        """Resume the workflow."""
        self.resume_button.click()
        self.page.wait_for_load_state("networkidle")

    def cancel_workflow(self) -> None:
        """Cancel the workflow."""
        self.cancel_button.click()
        self.page.wait_for_load_state("networkidle")

    def is_pause_visible(self) -> bool:
        """Check if pause button is visible."""
        return self.pause_button.is_visible()

    def is_resume_visible(self) -> bool:
        """Check if resume button is visible."""
        return self.resume_button.is_visible()

    def click_validation_row(self, index: int) -> None:
        """Click on a validation row.

        Args:
            index: Row index (0-based)
        """
        self.validation_rows.nth(index).click()
        self.page.wait_for_load_state("networkidle")

    def go_back_to_list(self) -> None:
        """Navigate back to workflows list."""
        self.back_link.click()
        self.page.wait_for_load_state("networkidle")

    def has_error(self) -> bool:
        """Check if workflow has an error message.

        Returns:
            True if error message is visible
        """
        return self.error_message.is_visible()

    def get_error_message(self) -> Optional[str]:
        """Get error message text.

        Returns:
            Error message or None
        """
        if self.has_error():
            return self.error_message.inner_text()
        return None
