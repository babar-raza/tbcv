"""Tests for recommendation generation endpoint (P1-T01, P1-T02)."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


class TestRecommendationGeneration:
    """Test POST /api/recommendations/{validation_id}/generate endpoint."""

    def test_generate_recommendations_success(self, client, mock_db_manager, mock_agent_registry):
        """Test successful recommendation generation."""
        validation_id = "test-validation-123"

        # Mock validation exists
        mock_validation = MagicMock()
        mock_validation.validation_results = {"issues": [{"level": "error", "category": "seo", "message": "Missing title"}]}
        mock_validation.file_path = "/test/file.md"
        mock_db_manager.get_validation_result.return_value = mock_validation
        mock_db_manager.list_recommendations.return_value = []

        # Mock recommendation agent
        mock_agent = MagicMock()
        mock_agent.process_request = AsyncMock(return_value={
            "count": 3,
            "recommendations": [{"id": "rec1"}, {"id": "rec2"}, {"id": "rec3"}]
        })
        mock_agent_registry.get_agent.return_value = mock_agent

        with patch('api.server.db_manager', mock_db_manager), \
             patch('api.server.agent_registry', mock_agent_registry), \
             patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value="test content"))), __exit__=MagicMock()))):
            response = client.post(f"/api/recommendations/{validation_id}/generate")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_generate_recommendations_validation_not_found(self, client, mock_db_manager):
        """Test generation fails when validation not found."""
        mock_db_manager.get_validation_result.return_value = None

        with patch('api.server.db_manager', mock_db_manager):
            response = client.post("/api/recommendations/nonexistent/generate")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_recommendations_already_exist_no_force(self, client, mock_db_manager):
        """Test generation skipped when recommendations exist and force=false."""
        mock_validation = MagicMock()
        mock_db_manager.get_validation_result.return_value = mock_validation
        mock_db_manager.list_recommendations.return_value = [MagicMock(), MagicMock()]

        with patch('api.server.db_manager', mock_db_manager):
            response = client.post("/api/recommendations/test-id/generate")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already has" in data["message"]

    def test_generate_recommendations_force_regenerate(self, client, mock_db_manager, mock_agent_registry):
        """Test force regeneration when recommendations exist."""
        mock_validation = MagicMock()
        mock_validation.validation_results = {"issues": []}
        mock_validation.file_path = "/test.md"
        mock_db_manager.get_validation_result.return_value = mock_validation
        mock_db_manager.list_recommendations.return_value = [MagicMock()]

        mock_agent = MagicMock()
        mock_agent.process_request = AsyncMock(return_value={"count": 5, "recommendations": []})
        mock_agent_registry.get_agent.return_value = mock_agent

        with patch('api.server.db_manager', mock_db_manager), \
             patch('api.server.agent_registry', mock_agent_registry), \
             patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=""))), __exit__=MagicMock()))):
            response = client.post("/api/recommendations/test-id/generate?force=true")

        assert response.status_code == 200
        assert response.json()["success"] is True


class TestRecommendationRebuild:
    """Test POST /api/recommendations/{validation_id}/rebuild endpoint."""

    def test_rebuild_recommendations_success(self, client, mock_db_manager, mock_agent_registry):
        """Test successful recommendation rebuild."""
        # Mock existing recommendations
        mock_recs = [MagicMock(id="rec1"), MagicMock(id="rec2")]
        mock_db_manager.list_recommendations.return_value = mock_recs
        mock_db_manager.delete_recommendation.return_value = True

        # Mock validation
        mock_validation = MagicMock()
        mock_validation.validation_results = {"issues": []}
        mock_validation.file_path = "/test.md"
        mock_db_manager.get_validation_result.return_value = mock_validation

        # Mock agent
        mock_agent = MagicMock()
        mock_agent.process_request = AsyncMock(return_value={"count": 4, "recommendations": []})
        mock_agent_registry.get_agent.return_value = mock_agent

        with patch('api.server.db_manager', mock_db_manager), \
             patch('api.server.agent_registry', mock_agent_registry), \
             patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=""))), __exit__=MagicMock()))):
            response = client.post("/api/recommendations/test-id/rebuild")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2

    def test_rebuild_recommendations_no_existing(self, client, mock_db_manager, mock_agent_registry):
        """Test rebuild when no existing recommendations."""
        mock_db_manager.list_recommendations.return_value = []

        mock_validation = MagicMock()
        mock_validation.validation_results = {"issues": []}
        mock_validation.file_path = "/test.md"
        mock_db_manager.get_validation_result.return_value = mock_validation

        mock_agent = MagicMock()
        mock_agent.process_request = AsyncMock(return_value={"count": 2, "recommendations": []})
        mock_agent_registry.get_agent.return_value = mock_agent

        with patch('api.server.db_manager', mock_db_manager), \
             patch('api.server.agent_registry', mock_agent_registry), \
             patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=""))), __exit__=MagicMock()))):
            response = client.post("/api/recommendations/test-id/rebuild")

        assert response.status_code == 200
        assert response.json()["deleted_count"] == 0


@pytest.fixture
def mock_db_manager():
    """Create a mock db_manager."""
    return MagicMock()


@pytest.fixture
def mock_agent_registry():
    """Create a mock agent_registry."""
    return MagicMock()


@pytest.fixture
def client():
    """Create a test client."""
    from api.server import app
    return TestClient(app)
