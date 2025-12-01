"""Page Object Models for Playwright UI tests."""
from .base_page import BasePage
from .dashboard_home import DashboardHome
from .validations_page import ValidationsPage
from .validation_detail import ValidationDetailPage
from .recommendations_page import RecommendationsPage
from .recommendation_detail import RecommendationDetailPage
from .workflows_page import WorkflowsPage
from .workflow_detail import WorkflowDetailPage

__all__ = [
    "BasePage",
    "DashboardHome",
    "ValidationsPage",
    "ValidationDetailPage",
    "RecommendationsPage",
    "RecommendationDetailPage",
    "WorkflowsPage",
    "WorkflowDetailPage",
]
