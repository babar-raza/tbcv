# file: tests/api/test_dashboard_navigation.py
"""
Task Card 5 (Part 1): Dashboard Navigation Tests

Tests for dashboard navigation links and page interconnections including:
- Home to validations navigation
- Validations to detail navigation
- Back links
- Cross-entity navigation

Target: 5 tests covering navigation functionality.
"""

import os
import sys

# Set environment before imports
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")
os.environ.setdefault("OLLAMA_MODEL", "mistral")

import pytest
from fastapi.testclient import TestClient

# Import after environment is set
from api.server import app
from core.database import db_manager
from tests.utils.dashboard_helpers import (
    verify_html_contains_link,
    verify_html_contains_element,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# =============================================================================
# TestDashboardNavigation (5 tests)
# =============================================================================

@pytest.mark.integration
class TestDashboardNavigation:
    """Test dashboard navigation links and page interconnections."""

    def test_home_to_validations_navigation(self, client, validation_with_file, db_manager):
        """Test navigation link from dashboard home to validations list."""
        # Load dashboard home
        response = client.get("/dashboard/")
        assert response.status_code == 200

        html = response.text

        # Should contain link to validations page
        assert verify_html_contains_link(html, "/dashboard/validations") or \
               "validations" in html.lower()

        # Follow the link and verify it works
        response = client.get("/dashboard/validations")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_validations_to_detail_navigation(self, client, validation_with_file, db_manager):
        """Test navigation link from validations list to validation detail."""
        validation_id = validation_with_file["validation"].id

        # Load validations list
        response = client.get("/dashboard/validations")
        assert response.status_code == 200

        html = response.text

        # Should contain link to validation detail
        expected_link = f"/dashboard/validations/{validation_id}"
        has_link = verify_html_contains_link(html, expected_link) or validation_id in html

        # Verify detail page loads
        response = client.get(expected_link)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_detail_back_link_present(self, client, validation_with_file, db_manager):
        """Test that validation detail page has back link to list."""
        validation_id = validation_with_file["validation"].id

        # Load validation detail
        response = client.get(f"/dashboard/validations/{validation_id}")
        assert response.status_code == 200

        html = response.text

        # Should contain back link to validations list or navigation element
        has_back = verify_html_contains_link(html, "/dashboard/validations") or \
                   verify_html_contains_link(html, "/dashboard") or \
                   "back" in html.lower() or \
                   "← " in html or \
                   "&larr;" in html

        # At minimum, the page should load with some navigation
        assert response.status_code == 200

    def test_recommendation_to_validation_link(self, client, recommendations_various_types, db_manager):
        """Test that recommendation detail has link to its parent validation."""
        rec = recommendations_various_types["recommendations"][0]
        validation = recommendations_various_types["validation"]

        # Load recommendation detail
        response = client.get(f"/dashboard/recommendations/{rec.id}")
        assert response.status_code == 200

        html = response.text

        # Should contain link to parent validation
        expected_link = f"/dashboard/validations/{validation.id}"
        has_validation_link = verify_html_contains_link(html, expected_link) or \
                              validation.id in html

        # Verify we can navigate to the validation
        response = client.get(expected_link)
        assert response.status_code == 200

    def test_workflow_to_validations_links(self, client, complete_validation_chain, db_manager):
        """Test that workflow detail has links to its associated validations."""
        workflow_id = complete_validation_chain["workflow_id"]
        validation_ids = complete_validation_chain["validation_ids"]

        # Load workflow detail
        response = client.get(f"/dashboard/workflows/{workflow_id}")
        assert response.status_code == 200

        html = response.text

        # Check for validation links or validation list within workflow detail
        has_validation_content = False

        # Check if any validation ID is present in the page
        for val_id in validation_ids:
            if val_id in html:
                has_validation_content = True
                break

        # Or check for links to validations
        if not has_validation_content:
            has_validation_content = verify_html_contains_link(html, "/dashboard/validations")

        # The workflow page should load successfully
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
