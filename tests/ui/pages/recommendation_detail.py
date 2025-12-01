"""Recommendation detail page object model."""
from typing import Optional
from playwright.sync_api import Locator, expect
from .base_page import BasePage


class RecommendationDetailPage(BasePage):
    """Recommendation detail page with review form."""

    URL_PATH = "/dashboard/recommendations/{id}"

    def navigate_to(self, recommendation_id: int) -> "RecommendationDetailPage":
        """Navigate to a specific recommendation.

        Args:
            recommendation_id: ID of the recommendation to view

        Returns:
            Self for method chaining
        """
        self.page.goto(f"{self.base_url}/dashboard/recommendations/{recommendation_id}")
        self.page.wait_for_load_state("networkidle")
        return self

    @property
    def status_badge(self) -> Locator:
        """Status badge."""
        return self.page.locator(".badge, .status, [class*='badge'], [class*='status']").first

    @property
    def title_display(self) -> Locator:
        """Recommendation title display."""
        return self.page.locator("h1, h2, .title, [class*='title']").first

    @property
    def type_badge(self) -> Locator:
        """Recommendation type badge."""
        return self.page.locator("[class*='type'], .type").first

    @property
    def confidence_display(self) -> Locator:
        """Confidence score display."""
        return self.page.locator("[class*='confidence'], .confidence").first

    @property
    def source_context(self) -> Locator:
        """Source file context viewer."""
        return self.page.locator("pre, code, [class*='source'], [class*='context'], .source-context").first

    @property
    def original_content(self) -> Locator:
        """Original content display."""
        return self.page.locator("[class*='original'], .original").first

    @property
    def proposed_content(self) -> Locator:
        """Proposed content display."""
        return self.page.locator("[class*='proposed'], .proposed").first

    @property
    def related_recommendations(self) -> Locator:
        """Related recommendations section."""
        return self.page.locator("[class*='related'], .related-recommendations").first

    @property
    def related_recommendations_list(self) -> Locator:
        """Related recommendations list items."""
        return self.related_recommendations.locator("li, a, .item")

    @property
    def audit_trail(self) -> Locator:
        """Audit trail/history section."""
        return self.page.locator("[class*='audit'], [class*='history'], .audit-trail").first

    @property
    def review_form(self) -> Locator:
        """Review form."""
        return self.page.locator("form").first

    @property
    def approve_radio(self) -> Locator:
        """Approve button (named 'radio' for backwards compat)."""
        return self.page.locator("button:has-text('Approve')").first

    @property
    def reject_radio(self) -> Locator:
        """Reject button (named 'radio' for backwards compat)."""
        return self.page.locator("button:has-text('Reject')").first

    @property
    def pending_radio(self) -> Locator:
        """Pending button (named 'radio' for backwards compat)."""
        return self.page.locator("button:has-text('Pending')").first

    @property
    def approve_button(self) -> Locator:
        """Approve button."""
        return self.page.locator("button:has-text('Approve')").first

    @property
    def reject_button(self) -> Locator:
        """Reject button."""
        return self.page.locator("button:has-text('Reject')").first

    @property
    def reviewer_field(self) -> Locator:
        """Reviewer name input field."""
        return self.page.locator("input[name='reviewer'], input[id*='reviewer']").first

    @property
    def notes_field(self) -> Locator:
        """Notes textarea."""
        return self.page.locator("textarea[name='notes'], textarea[id*='notes'], textarea").first

    @property
    def submit_button(self) -> Locator:
        """Submit review button."""
        return self.page.get_by_role("button", name="Submit")

    @property
    def back_link(self) -> Locator:
        """Back to list link."""
        return self.page.get_by_role("link", name="Back")

    @property
    def validation_link(self) -> Locator:
        """Link to parent validation."""
        return self.page.locator("a[href*='validations']").first

    def approve_recommendation(self, notes: str = "", reviewer: str = "") -> None:
        """Approve the recommendation.

        Args:
            notes: Optional notes for the review
            reviewer: Optional reviewer name
        """
        # Fill form fields first
        if reviewer:
            self.reviewer_field.fill(reviewer)
        if notes:
            self.notes_field.fill(notes)
        # Click approve button (which submits via JS)
        self.approve_button.click()
        self.page.wait_for_load_state("networkidle")

    def reject_recommendation(self, notes: str = "", reviewer: str = "") -> None:
        """Reject the recommendation.

        Args:
            notes: Optional notes for the review
            reviewer: Optional reviewer name
        """
        # Fill form fields first
        if reviewer:
            self.reviewer_field.fill(reviewer)
        if notes:
            self.notes_field.fill(notes)
        # Click reject button (which submits via JS)
        self.reject_button.click()
        self.page.wait_for_load_state("networkidle")

    def set_pending(self, notes: str = "") -> None:
        """Set recommendation back to pending.

        Args:
            notes: Optional notes
        """
        if notes:
            self.notes_field.fill(notes)
        self.pending_radio.click()
        self.page.wait_for_load_state("networkidle")

    def get_status(self) -> str:
        """Get current status.

        Returns:
            Status text
        """
        return self.status_badge.inner_text().strip().lower()

    def get_title(self) -> str:
        """Get recommendation title.

        Returns:
            Title text
        """
        return self.title_display.inner_text().strip()

    def has_source_context(self) -> bool:
        """Check if source context is displayed.

        Returns:
            True if source context is visible
        """
        return self.source_context.is_visible()

    def has_related_recommendations(self) -> bool:
        """Check if related recommendations section is visible.

        Returns:
            True if related section is visible
        """
        return self.related_recommendations.is_visible()

    def get_related_count(self) -> int:
        """Get number of related recommendations.

        Returns:
            Count of related recommendations
        """
        if not self.has_related_recommendations():
            return 0
        return self.related_recommendations_list.count()

    def click_related_recommendation(self, index: int = 0) -> None:
        """Click on a related recommendation.

        Args:
            index: Index of related recommendation to click
        """
        self.related_recommendations_list.nth(index).click()
        self.page.wait_for_load_state("networkidle")

    def go_to_validation(self) -> None:
        """Navigate to parent validation."""
        self.validation_link.click()
        self.page.wait_for_load_state("networkidle")

    def go_back_to_list(self) -> None:
        """Navigate back to recommendations list."""
        self.back_link.click()
        self.page.wait_for_load_state("networkidle")

    def is_review_form_visible(self) -> bool:
        """Check if review form is visible.

        Returns:
            True if form is visible
        """
        return self.review_form.is_visible()
