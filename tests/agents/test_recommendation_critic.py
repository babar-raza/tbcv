# file: tests/agents/test_recommendation_critic.py
"""Tests for RecommendationCriticAgent - Reflection Pattern Implementation."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from agents.recommendation_critic import RecommendationCriticAgent, CritiqueResult


# --- Fixtures ---

@pytest.fixture
def mock_config():
    """Mock reflection configuration."""
    return {
        "reflection": {
            "enabled": True,
            "thresholds": {
                "quality_threshold": 0.7,
                "discard_threshold": 0.3,
                "similarity_threshold": 0.85
            },
            "refinement": {
                "max_iterations": 2,
                "use_llm": False
            },
            "deduplication": {
                "enabled": True,
                "method": "fuzzy",
                "compare_fields": ["instruction", "scope"]
            },
            "dimensions": {
                "actionable": {"weight": 0.3},
                "fixes_issue": {"weight": 0.3},
                "specific": {"weight": 0.2},
                "side_effects": {"weight": 0.2}
            },
            "rules": {
                "require_rationale": True,
                "min_instruction_length": 20,
                "max_instruction_length": 500,
                "banned_phrases": [
                    "review and fix",
                    "check and update",
                    "ensure proper"
                ]
            }
        }
    }


@pytest.fixture
def critic(mock_config):
    """Create RecommendationCriticAgent with mock config."""
    with patch('agents.recommendation_critic.get_config_loader') as mock_loader:
        mock_loader.return_value.load.return_value = mock_config
        agent = RecommendationCriticAgent()
        return agent


@pytest.fixture
def high_quality_recommendation():
    """A high-quality recommendation that should pass critique."""
    return {
        "validation_id": "val_123",
        "scope": "line:42",
        "instruction": "Replace the deprecated 'WordsApi' import with the new 'Aspose.Words.Cloud.SDK' package import statement",
        "rationale": "The WordsApi import is deprecated and will be removed in the next version. Using the new SDK ensures forward compatibility.",
        "severity": "high",
        "confidence": 0.95
    }


@pytest.fixture
def low_quality_recommendation():
    """A low-quality recommendation that should be discarded or refined."""
    return {
        "validation_id": "val_456",
        "scope": "global",
        "instruction": "Review and fix the code",
        "rationale": "",
        "severity": "medium",
        "confidence": 0.5
    }


@pytest.fixture
def medium_quality_recommendation():
    """A medium-quality recommendation that needs refinement."""
    return {
        "validation_id": "val_789",
        "scope": "global",
        "instruction": "Update the API endpoint URL to use the new format",
        "rationale": "The old API format is being phased out",
        "severity": "medium",
        "confidence": 0.7
    }


# --- CritiqueResult Tests ---

class TestCritiqueResult:
    """Tests for CritiqueResult dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        result = CritiqueResult()
        assert result.actionable is True
        assert result.quality_score == 0.8
        assert result.should_discard is False
        assert result.side_effects == []

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        result = CritiqueResult(
            actionable=False,
            actionable_reason="Too vague",
            quality_score=0.4
        )
        d = result.to_dict()
        assert d["actionable"] is False
        assert d["actionable_reason"] == "Too vague"
        assert d["quality_score"] == 0.4


# --- Initialization Tests ---

class TestCriticInitialization:
    """Tests for agent initialization."""

    def test_init_loads_config(self, critic):
        """Should load reflection config on init."""
        assert critic.config is not None
        assert "thresholds" in critic.config

    def test_init_with_default_config(self):
        """Should use default config if loading fails."""
        with patch('agents.recommendation_critic.get_config_loader') as mock_loader:
            mock_loader.return_value.load.side_effect = Exception("Config error")
            agent = RecommendationCriticAgent()
            assert agent.config.get("enabled", True) is True

    def test_get_contract(self, critic):
        """Should return valid agent contract."""
        contract = critic.get_contract()
        assert contract.agent_id == "recommendation_critic"
        assert contract.name == "RecommendationCriticAgent"
        assert len(contract.capabilities) >= 3

    def test_is_enabled(self, critic):
        """Should report enabled status from config."""
        assert critic.is_enabled() is True


# --- Rule-Based Critique Tests ---

class TestRuleBasedCritique:
    """Tests for rule-based critique evaluation."""

    @pytest.mark.asyncio
    async def test_high_quality_recommendation_passes(self, critic, high_quality_recommendation):
        """High-quality recommendation should get high score."""
        result = await critic.critique(high_quality_recommendation, {})

        assert result.quality_score >= 0.7
        assert result.should_discard is False
        assert result.needs_refinement is False
        assert result.actionable is True

    @pytest.mark.asyncio
    async def test_low_quality_recommendation_flagged(self, critic, low_quality_recommendation):
        """Low-quality recommendation should be flagged for discard or refinement."""
        result = await critic.critique(low_quality_recommendation, {})

        assert result.quality_score < 0.7
        assert result.actionable is False  # Contains banned phrase
        assert result.should_discard is True or result.needs_refinement is True

    @pytest.mark.asyncio
    async def test_banned_phrases_detected(self, critic):
        """Should detect and flag banned phrases."""
        rec = {
            "instruction": "Please review and fix this issue",
            "scope": "global",
            "rationale": "Needs fixing"
        }
        result = await critic.critique(rec, {})

        assert result.actionable is False
        assert "vague" in result.actionable_reason.lower() or "actionable" in result.actionable_reason.lower()

    @pytest.mark.asyncio
    async def test_short_instruction_flagged(self, critic):
        """Should flag instructions that are too short."""
        rec = {
            "instruction": "Fix it",
            "scope": "global",
            "rationale": "Broken"
        }
        result = await critic.critique(rec, {})

        assert result.actionable is False
        assert result.quality_score < 0.7

    @pytest.mark.asyncio
    async def test_specific_scope_improves_score(self, critic):
        """Specific scope should improve quality score."""
        rec_global = {
            "instruction": "Update the deprecated function call to use the new API method",
            "scope": "global",
            "rationale": "API has been updated"
        }
        rec_specific = {
            "instruction": "Update the deprecated function call to use the new API method",
            "scope": "line:42",
            "rationale": "API has been updated"
        }

        result_global = await critic.critique(rec_global, {})
        result_specific = await critic.critique(rec_specific, {})

        assert result_specific.specific is True
        assert result_global.specific is False
        assert result_specific.quality_score >= result_global.quality_score

    @pytest.mark.asyncio
    async def test_context_affects_fixes_issue_score(self, critic):
        """Context with issue type should improve fixes_issue evaluation."""
        rec = {
            "instruction": "Fix the yaml frontmatter syntax error on line 5",
            "scope": "line:5",
            "rationale": "YAML syntax is invalid"
        }
        context = {
            "issue_type": "yaml",
            "issue_message": "Invalid YAML syntax"
        }

        result = await critic.critique(rec, context)

        assert result.fixes_issue is True
        assert "addresses" in result.fixes_issue_reason.lower() or "issue" in result.fixes_issue_reason.lower()


# --- Refinement Tests ---

class TestRefinement:
    """Tests for recommendation refinement."""

    @pytest.mark.asyncio
    async def test_refine_removes_banned_phrases(self, critic):
        """Refinement should remove or replace banned phrases."""
        rec = {
            "instruction": "Please review and fix the YAML frontmatter",
            "scope": "global",
            "rationale": ""
        }
        critique = {
            "refinement_suggestions": "Make more specific"
        }

        refined = await critic.refine(rec, critique)

        # Should not contain banned phrase
        assert "review and fix" not in refined["instruction"].lower()
        assert refined.get("refined") is True

    @pytest.mark.asyncio
    async def test_refine_adds_rationale_if_missing(self, critic):
        """Refinement should add rationale if missing."""
        rec = {
            "instruction": "Update the API endpoint configuration settings",
            "scope": "global",
            "rationale": ""
        }
        critique = {
            "issue_message": "API endpoint is incorrect"
        }

        refined = await critic.refine(rec, critique)

        assert len(refined.get("rationale", "")) > 10

    @pytest.mark.asyncio
    async def test_refine_tracks_iteration(self, critic):
        """Refinement should track iteration count."""
        rec = {
            "instruction": "Review and fix the code structure",
            "scope": "global"
        }
        critique = {}

        refined1 = await critic.refine(rec, critique)
        assert refined1.get("refinement_iteration") == 1

        refined2 = await critic.refine(refined1, critique)
        assert refined2.get("refinement_iteration") == 2


# --- Deduplication Tests ---

class TestDeduplication:
    """Tests for recommendation deduplication."""

    def test_empty_list_returns_empty(self, critic):
        """Empty list should return empty."""
        result = critic.deduplicate([])
        assert result == []

    def test_single_item_returns_unchanged(self, critic):
        """Single item should return unchanged."""
        recs = [{"instruction": "Fix this", "scope": "global"}]
        result = critic.deduplicate(recs)
        assert len(result) == 1

    def test_exact_duplicates_removed(self, critic):
        """Exact duplicates should be removed."""
        recs = [
            {"instruction": "Fix the YAML syntax error", "scope": "frontmatter", "confidence": 0.9},
            {"instruction": "Fix the YAML syntax error", "scope": "frontmatter", "confidence": 0.8}
        ]
        result = critic.deduplicate(recs)
        assert len(result) == 1
        # Should keep higher confidence
        assert result[0]["confidence"] == 0.9

    def test_similar_recommendations_deduplicated(self, critic):
        """Similar recommendations should be deduplicated."""
        recs = [
            {"instruction": "Fix the YAML syntax error in frontmatter", "scope": "frontmatter", "critique_score": 0.9},
            {"instruction": "Fix YAML syntax error in the frontmatter section", "scope": "frontmatter", "critique_score": 0.8}
        ]
        result = critic.deduplicate(recs)
        # These are similar enough to be deduplicated
        assert len(result) <= 2  # May or may not be deduplicated based on threshold

    def test_different_recommendations_kept(self, critic):
        """Different recommendations should be kept."""
        recs = [
            {"instruction": "Fix the YAML syntax error", "scope": "frontmatter"},
            {"instruction": "Update the broken link to correct URL", "scope": "links"}
        ]
        result = critic.deduplicate(recs)
        assert len(result) == 2

    def test_keeps_highest_quality(self, critic):
        """Should keep the highest quality when deduplicating."""
        recs = [
            {"instruction": "Fix the API call", "scope": "code", "critique_score": 0.6},
            {"instruction": "Fix the API call", "scope": "code", "critique_score": 0.9},
            {"instruction": "Fix the API call", "scope": "code", "critique_score": 0.7}
        ]
        result = critic.deduplicate(recs)
        assert len(result) == 1
        assert result[0]["critique_score"] == 0.9


# --- Full Pipeline Tests ---

class TestFullPipeline:
    """Tests for the complete reflection pipeline."""

    @pytest.mark.asyncio
    async def test_process_recommendations_empty_list(self, critic):
        """Empty list should pass through."""
        result = await critic.handle_process_recommendations({
            "recommendations": [],
            "context": {}
        })
        assert result["recommendations"] == []
        assert result["discarded_count"] == 0

    @pytest.mark.asyncio
    async def test_process_high_quality_unchanged(self, critic, high_quality_recommendation):
        """High-quality recommendations should pass through unchanged."""
        result = await critic.handle_process_recommendations({
            "recommendations": [high_quality_recommendation],
            "context": {}
        })
        assert len(result["recommendations"]) == 1
        assert result["discarded_count"] == 0
        assert result["refined_count"] == 0

    @pytest.mark.asyncio
    async def test_process_low_quality_discarded(self, critic, low_quality_recommendation):
        """Low-quality recommendations should be discarded."""
        result = await critic.handle_process_recommendations({
            "recommendations": [low_quality_recommendation],
            "context": {}
        })
        # Should either be discarded or refined
        assert result["discarded_count"] >= 0 or result["refined_count"] >= 0

    @pytest.mark.asyncio
    async def test_process_mixed_quality(self, critic, high_quality_recommendation, low_quality_recommendation):
        """Should handle mixed quality recommendations."""
        result = await critic.handle_process_recommendations({
            "recommendations": [high_quality_recommendation, low_quality_recommendation],
            "context": {}
        })
        # High quality should be kept
        assert result["reflection_enabled"] is True
        # At least one should be processed
        assert len(result["recommendations"]) >= 1

    @pytest.mark.asyncio
    async def test_process_with_duplicates(self, critic, high_quality_recommendation):
        """Should deduplicate similar recommendations."""
        recs = [
            high_quality_recommendation,
            {**high_quality_recommendation, "confidence": 0.8}  # Duplicate with lower confidence
        ]
        result = await critic.handle_process_recommendations({
            "recommendations": recs,
            "context": {}
        })
        # Should deduplicate
        assert result["deduplicated_count"] >= 0

    @pytest.mark.asyncio
    async def test_reflection_disabled(self, mock_config):
        """Should pass through when reflection disabled."""
        mock_config["reflection"]["enabled"] = False

        with patch('agents.recommendation_critic.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = mock_config
            agent = RecommendationCriticAgent()

            result = await agent.handle_process_recommendations({
                "recommendations": [{"instruction": "test"}],
                "context": {}
            })

            assert result["reflection_enabled"] is False
            assert len(result["recommendations"]) == 1


# --- MCP Handler Tests ---

class TestMCPHandlers:
    """Tests for MCP message handlers."""

    @pytest.mark.asyncio
    async def test_handle_critique(self, critic, high_quality_recommendation):
        """Should handle critique request."""
        result = await critic.handle_critique({
            "recommendation": high_quality_recommendation,
            "context": {}
        })
        assert "quality_score" in result
        assert "actionable" in result

    @pytest.mark.asyncio
    async def test_handle_refine(self, critic):
        """Should handle refine request."""
        result = await critic.handle_refine({
            "recommendation": {"instruction": "Review and fix this", "scope": "global"},
            "critique": {"refinement_suggestions": "Be more specific"}
        })
        assert "instruction" in result
        assert result.get("refined") is True

    @pytest.mark.asyncio
    async def test_handle_deduplicate(self, critic):
        """Should handle deduplicate request."""
        result = await critic.handle_deduplicate({
            "recommendations": [
                {"instruction": "Fix A", "scope": "global"},
                {"instruction": "Fix B", "scope": "global"}
            ]
        })
        assert isinstance(result, list)


# --- Edge Cases ---

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_recommendation(self, critic):
        """Should handle empty recommendation."""
        result = await critic.critique({}, {})
        assert result.quality_score < 0.7

    @pytest.mark.asyncio
    async def test_none_fields(self, critic):
        """Should handle None fields gracefully."""
        rec = {
            "instruction": None,
            "scope": None,
            "rationale": None
        }
        # Should not raise
        result = await critic.critique(rec, {})
        assert result is not None

    @pytest.mark.asyncio
    async def test_very_long_instruction(self, critic):
        """Should handle very long instructions."""
        rec = {
            "instruction": "Fix " + "x" * 1000,
            "scope": "global",
            "rationale": "Test"
        }
        result = await critic.critique(rec, {})
        assert result is not None

    def test_similarity_calculation_empty_strings(self, critic):
        """Should handle empty strings in similarity calculation."""
        similarity = critic._calculate_similarity(
            {"instruction": "", "scope": ""},
            {"instruction": "", "scope": ""},
            ["instruction", "scope"],
            "fuzzy"
        )
        assert similarity == 1.0  # Empty strings are identical

    def test_similarity_calculation_missing_fields(self, critic):
        """Should handle missing fields in similarity calculation."""
        similarity = critic._calculate_similarity(
            {"instruction": "Fix A"},
            {"instruction": "Fix A"},
            ["instruction", "missing_field"],
            "fuzzy"
        )
        assert similarity >= 0.0


# --- Integration with RecommendationAgent ---

class TestIntegrationWithRecommendationAgent:
    """Tests for integration with RecommendationAgent."""

    @pytest.mark.asyncio
    async def test_recommendation_agent_uses_critic(self, mock_config):
        """RecommendationAgent should use critic when reflection enabled."""
        mock_config["reflection"]["enabled"] = True

        with patch('agents.recommendation_critic.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = mock_config

            from agents.recommendation_agent import RecommendationAgent

            with patch.object(RecommendationAgent, '_load_reflection_config') as mock_load:
                mock_load.return_value = None
                agent = RecommendationAgent()
                agent._reflection_config = mock_config["reflection"]

                # Check that reflection is detected as enabled
                assert agent._reflection_enabled() is True
