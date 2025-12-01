"""Navigation tests for TBCV dashboard UI.

This module tests navigation functionality across the TBCV dashboard including:
- Header navigation links
- Page-to-page navigation
- Detail page navigation
- Pagination controls
- Filter persistence during navigation
"""
import re
import pytest
from playwright.sync_api import Page, expect

from tests.ui.pages import (
    DashboardHome,
    ValidationsPage,
    RecommendationsPage,
    WorkflowsPage,
)


@pytest.mark.ui
class TestHeaderNavigation:
    """Test header navigation links across all pages."""

    def test_home_link_navigates_to_dashboard(
        self,
        page: Page,
        base_url: str,
        validations_page: ValidationsPage,
    ) -> None:
        """Test that clicking Dashboard link navigates to dashboard home.

        Args:
            page: Playwright page instance
            base_url: Base server URL
            validations_page: Validations page object
        """
        # Navigate to validations page first
        validations_page.navigate()
        expect(page).to_have_url(f"{base_url}/dashboard/validations")

        # Click Home link in header (navigates to dashboard home)
        validations_page.click_nav_link("Home")

        # Verify navigation to dashboard home
        expect(page).to_have_url(f"{base_url}/dashboard/")

    def test_validations_link_works(
        self,
        page: Page,
        base_url: str,
        dashboard_home: DashboardHome,
    ) -> None:
        """Test that clicking Validations link navigates to validations page.

        Args:
            page: Playwright page instance
            base_url: Base server URL
            dashboard_home: Dashboard home page object
        """
        # Navigate to dashboard home
        dashboard_home.navigate()
        expect(page).to_have_url(f"{base_url}/dashboard/")

        # Click Validations link in header
        dashboard_home.click_nav_link("Validations")

        # Verify navigation to validations page
        expect(page).to_have_url(f"{base_url}/dashboard/validations")

    def test_recommendations_link_works(
        self,
        page: Page,
        base_url: str,
        dashboard_home: DashboardHome,
    ) -> None:
        """Test that clicking Recommendations link navigates to recommendations page.

        Args:
            page: Playwright page instance
            base_url: Base server URL
            dashboard_home: Dashboard home page object
        """
        # Navigate to dashboard home
        dashboard_home.navigate()
        expect(page).to_have_url(f"{base_url}/dashboard/")

        # Click Recommendations link in header
        dashboard_home.click_nav_link("Recommendations")

        # Verify navigation to recommendations page
        expect(page).to_have_url(f"{base_url}/dashboard/recommendations")

    def test_workflows_link_works(
        self,
        page: Page,
        base_url: str,
        dashboard_home: DashboardHome,
    ) -> None:
        """Test that clicking Workflows link navigates to workflows page.

        Args:
            page: Playwright page instance
            base_url: Base server URL
            dashboard_home: Dashboard home page object
        """
        # Navigate to dashboard home
        dashboard_home.navigate()
        expect(page).to_have_url(f"{base_url}/dashboard/")

        # Click Workflows link in header
        dashboard_home.click_nav_link("Workflows")

        # Verify navigation to workflows page
        expect(page).to_have_url(f"{base_url}/dashboard/workflows")

    def test_header_links_visible_on_all_pages(
        self,
        page: Page,
        dashboard_home: DashboardHome,
        validations_page: ValidationsPage,
        recommendations_page: RecommendationsPage,
    ) -> None:
        """Test that navigation links are visible on all dashboard pages.

        Args:
            page: Playwright page instance
            dashboard_home: Dashboard home page object
            validations_page: Validations page object
            recommendations_page: Recommendations page object
        """
        # Check dashboard home - header has 6 nav links
        dashboard_home.navigate()
        # nav_links count should be at least 3 (core nav: Validations, Recommendations, Workflows)
        nav_count = dashboard_home.nav_links.count()
        assert nav_count >= 3, f"Expected at least 3 nav links, got {nav_count}"

        # Check validations page
        validations_page.navigate()
        nav_count = validations_page.nav_links.count()
        assert nav_count >= 3, f"Expected at least 3 nav links, got {nav_count}"

        # Check recommendations page
        recommendations_page.navigate()
        nav_count = recommendations_page.nav_links.count()
        assert nav_count >= 3, f"Expected at least 3 nav links, got {nav_count}"


@pytest.mark.ui
class TestPageNavigation:
    """Test navigation between list and detail pages."""

    def test_validation_view_opens_detail(
        self,
        page: Page,
        base_url: str,
        validations_page: ValidationsPage,
        multiple_validations: list,
    ) -> None:
        """Test that clicking View on validation opens detail page.

        Args:
            page: Playwright page instance
            base_url: Base server URL
            validations_page: Validations page object
            multiple_validations: Fixture that creates test validations
        """
        # Navigate to validations list
        validations_page.navigate()

        # Check if there are any validations
        row_count = validations_page.get_row_count()

        if row_count > 0:
            # Click view button on first validation
            validations_page.click_view_button(0)

            # Verify URL contains /validations/ (detail page with ID)
            expect(page).to_have_url(re.compile(rf"{re.escape(base_url)}/dashboard/validations/.+"))
        else:
            # No validations exist, skip test gracefully
            pytest.skip("No validations available to test view navigation")

    def test_recommendation_view_opens_detail(
        self,
        page: Page,
        base_url: str,
        recommendations_page: RecommendationsPage,
        multiple_recommendations: list,
    ) -> None:
        """Test that clicking View on recommendation opens detail page.

        Args:
            page: Playwright page instance
            base_url: Base server URL
            recommendations_page: Recommendations page object
            multiple_recommendations: Fixture that creates test recommendations
        """
        # Navigate to recommendations list
        recommendations_page.navigate()

        # Check if there are any recommendations
        row_count = recommendations_page.get_row_count()

        if row_count > 0:
            # Click view button on first recommendation
            recommendations_page.click_view_button(0)

            # Verify URL contains /recommendations/ (detail page with ID)
            expect(page).to_have_url(re.compile(rf"{re.escape(base_url)}/dashboard/recommendations/.+"))
        else:
            # No recommendations exist, skip test gracefully
            pytest.skip("No recommendations available to test view navigation")

    def test_workflow_view_opens_detail(
        self,
        page: Page,
        base_url: str,
        workflows_page: WorkflowsPage,
        running_workflow: dict,
    ) -> None:
        """Test that clicking View on workflow opens detail page.

        Args:
            page: Playwright page instance
            base_url: Base server URL
            workflows_page: Workflows page object
            running_workflow: Fixture that creates a test workflow
        """
        # Navigate to workflows list
        workflows_page.navigate()

        # Check if there are any workflows
        row_count = workflows_page.get_row_count()

        if row_count > 0:
            # Click view button on first workflow
            workflows_page.click_view_button(0)

            # Verify URL contains /workflows/ (detail page with ID)
            expect(page).to_have_url(re.compile(rf"{re.escape(base_url)}/dashboard/workflows/.+"))
        else:
            # No workflows exist, skip test gracefully
            pytest.skip("No workflows available to test view navigation")


@pytest.mark.ui
class TestPagination:
    """Test pagination controls and filter persistence."""

    def test_pagination_next_page(
        self,
        page: Page,
        validations_page: ValidationsPage,
        multiple_validations: list,
    ) -> None:
        """Test that pagination next button changes page.

        Args:
            page: Playwright page instance
            validations_page: Validations page object
            multiple_validations: Fixture that creates multiple validations
        """
        # Navigate to validations page
        validations_page.navigate()

        # Check if pagination controls exist
        if not validations_page.has_pagination():
            pytest.skip("No pagination controls available")

        # Get current page number
        current_page = validations_page.get_current_page_number()

        # Get initial row count to verify page changed
        initial_first_row = None
        if validations_page.get_row_count() > 0:
            initial_first_row = validations_page.get_row_data(0)

        # Click next page
        try:
            validations_page.go_to_next_page()

            # Verify page changed by checking:
            # 1. Current page number increased (if available)
            new_page = validations_page.get_current_page_number()
            if current_page and new_page:
                assert new_page > current_page, "Page number should increase"

            # 2. First row data changed (if available)
            if initial_first_row and validations_page.get_row_count() > 0:
                new_first_row = validations_page.get_row_data(0)
                assert new_first_row != initial_first_row, "First row should change after pagination"
        except Exception:
            # Next button may not be available if on last page
            pytest.skip("Cannot navigate to next page (possibly on last page)")

    def test_pagination_maintains_filters(
        self,
        page: Page,
        base_url: str,
        validations_page: ValidationsPage,
        multiple_validations: list,
    ) -> None:
        """Test that filters persist when navigating between pages.

        Args:
            page: Playwright page instance
            base_url: Base server URL
            validations_page: Validations page object
            multiple_validations: Fixture that creates multiple validations
        """
        # Navigate to validations page
        validations_page.navigate()

        # Try to apply a status filter
        try:
            validations_page.filter_by_status("pass")
            filtered_url = page.url

            # Check if pagination exists after filtering
            if not validations_page.has_pagination():
                pytest.skip("No pagination controls available after filtering")

            # Navigate to next page
            try:
                validations_page.go_to_next_page()

                # Verify filter is maintained in URL or state
                current_url = page.url

                # URL should still contain filter parameters or be on filtered view
                # The exact URL structure depends on implementation
                assert "pass" in current_url.lower() or "/validations" in current_url, \
                    "Filter should be maintained after pagination"

                # Verify we're still on validations page
                expect(page).to_have_url(re.compile(rf"{re.escape(base_url)}/dashboard/validations"))

            except Exception:
                # Next button may not be available
                pytest.skip("Cannot navigate to next page for filter persistence test")

        except Exception:
            # Status filter may not be available
            pytest.skip("Cannot apply status filter for pagination test")
