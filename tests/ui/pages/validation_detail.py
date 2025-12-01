"""Validation detail page object model."""
from typing import List, Optional
from playwright.sync_api import Locator, expect
from .base_page import BasePage


class ValidationDetailPage(BasePage):
    """Validation detail page with approve/reject/enhance actions."""

    URL_PATH = "/dashboard/validations/{id}"

    def navigate_to(self, validation_id: int) -> "ValidationDetailPage":
        """Navigate to a specific validation.

        Args:
            validation_id: ID of the validation to view

        Returns:
            Self for method chaining
        """
        self.page.goto(f"{self.base_url}/dashboard/validations/{validation_id}")
        self.page.wait_for_load_state("networkidle")
        return self

    @property
    def status_badge(self) -> Locator:
        """Status badge element."""
        return self.page.locator(".badge, .status, [class*='badge'], [class*='status']").first

    @property
    def file_path_display(self) -> Locator:
        """File path display element."""
        return self.page.locator(".file-path, [class*='path'], code").first

    @property
    def severity_badge(self) -> Locator:
        """Severity badge element."""
        return self.page.locator("[class*='severity'], .severity").first

    @property
    def approve_button(self) -> Locator:
        """Approve button."""
        return self.page.get_by_role("button", name="Approve")

    @property
    def reject_button(self) -> Locator:
        """Reject button."""
        return self.page.get_by_role("button", name="Reject")

    @property
    def enhance_button(self) -> Locator:
        """Enhance button."""
        return self.page.get_by_role("button", name="Enhance")

    @property
    def recommendations_section(self) -> Locator:
        """Recommendations section container."""
        return self.page.locator("[class*='recommendation'], .recommendations, #recommendations").first

    @property
    def recommendations_table(self) -> Locator:
        """Recommendations table."""
        return self.recommendations_section.locator("table").first

    @property
    def recommendation_rows(self) -> Locator:
        """Recommendation table rows."""
        return self.recommendations_table.locator("tbody tr")

    @property
    def recommendation_checkboxes(self) -> Locator:
        """Recommendation selection checkboxes."""
        return self.page.locator("input[type='checkbox'][name*='recommendation'], input[type='checkbox'][id*='rec']")

    @property
    def enhance_selected_button(self) -> Locator:
        """Enhance selected recommendations button."""
        return self.page.get_by_role("button", name="Enhance Selected")

    @property
    def generate_recommendations_button(self) -> Locator:
        """Generate recommendations button."""
        return self.page.get_by_role("button", name="Generate")

    @property
    def rebuild_button(self) -> Locator:
        """Rebuild recommendations button."""
        return self.page.get_by_role("button", name="Rebuild")

    @property
    def back_link(self) -> Locator:
        """Back to list link."""
        return self.page.get_by_role("link", name="Back")

    @property
    def validation_results_section(self) -> Locator:
        """Validation results/details section."""
        return self.page.locator("[class*='results'], [class*='details'], .validation-results").first

    def approve_validation(self) -> None:
        """Approve the validation."""
        self.approve_button.click()
        self.page.wait_for_load_state("networkidle")

    def reject_validation(self) -> None:
        """Reject the validation."""
        self.reject_button.click()
        self.page.wait_for_load_state("networkidle")

    def enhance_validation(self) -> None:
        """Enhance the validation."""
        self.enhance_button.click()
        self.page.wait_for_load_state("networkidle")

    def select_recommendation(self, index: int) -> None:
        """Select a recommendation by index.

        Args:
            index: Recommendation index (0-based)
        """
        self.recommendation_checkboxes.nth(index).check()

    def deselect_recommendation(self, index: int) -> None:
        """Deselect a recommendation by index.

        Args:
            index: Recommendation index (0-based)
        """
        self.recommendation_checkboxes.nth(index).uncheck()

    def select_recommendations(self, indices: List[int]) -> None:
        """Select multiple recommendations.

        Args:
            indices: List of recommendation indices to select
        """
        for i in indices:
            self.select_recommendation(i)

    def select_all_recommendations(self) -> None:
        """Select all recommendation checkboxes."""
        count = self.recommendation_checkboxes.count()
        for i in range(count):
            self.recommendation_checkboxes.nth(i).check()

    def enhance_selected(self) -> None:
        """Enhance selected recommendations."""
        self.enhance_selected_button.click()
        self.page.wait_for_load_state("networkidle")

    def generate_recommendations(self) -> None:
        """Generate recommendations."""
        self.generate_recommendations_button.click()
        self.page.wait_for_load_state("networkidle")

    def rebuild_recommendations(self) -> None:
        """Rebuild recommendations."""
        self.rebuild_button.click()
        self.page.wait_for_load_state("networkidle")

    def get_status(self) -> str:
        """Get current validation status.

        Returns:
            Status text
        """
        return self.status_badge.inner_text().strip().lower()

    def get_recommendation_count(self) -> int:
        """Get number of recommendations.

        Returns:
            Number of recommendation rows
        """
        return self.recommendation_rows.count()

    def get_selected_recommendation_count(self) -> int:
        """Get number of selected recommendations.

        Returns:
            Number of checked checkboxes
        """
        count = 0
        total = self.recommendation_checkboxes.count()
        for i in range(total):
            if self.recommendation_checkboxes.nth(i).is_checked():
                count += 1
        return count

    def is_enhance_button_enabled(self) -> bool:
        """Check if enhance button is enabled.

        Returns:
            True if button is enabled
        """
        return self.enhance_button.is_enabled()

    def is_approve_button_visible(self) -> bool:
        """Check if approve button is visible.

        Returns:
            True if button is visible
        """
        return self.approve_button.is_visible()

    def click_recommendation_row(self, index: int) -> None:
        """Click on a recommendation row to view details.

        Args:
            index: Row index (0-based)
        """
        self.recommendation_rows.nth(index).click()
        self.page.wait_for_load_state("networkidle")

    def go_back_to_list(self) -> None:
        """Navigate back to validations list."""
        self.back_link.click()
        self.page.wait_for_load_state("networkidle")
