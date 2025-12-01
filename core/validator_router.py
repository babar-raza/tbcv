# file: core/validator_router.py
"""
ValidatorRouter - Tiered validation flow with parallel execution and user control.

Supports:
- Tiered execution (Tier 1 -> Tier 2 -> Tier 3)
- Parallel execution within tiers
- Dependency resolution between validators
- Early termination on critical errors
- User-configurable validator enable/disable
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Callable, TYPE_CHECKING
from datetime import datetime

from core.config_loader import get_config_loader, ConfigLoader
from core.logging import get_logger

if TYPE_CHECKING:
    from agents.validators.base_validator import ValidationResult

logger = get_logger(__name__)


@dataclass
class TierResult:
    """Result from executing a single tier."""
    tier_name: str
    tier_number: int
    validators_run: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    duration_ms: float = 0.0
    terminated_early: bool = False


@dataclass
class FlowResult:
    """Result from executing the full validation flow."""
    tiers_executed: List[TierResult] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    routing_info: Dict[str, str] = field(default_factory=dict)
    total_critical: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    terminated_early: bool = False
    termination_reason: str = ""
    total_duration_ms: float = 0.0


class ValidatorRouter:
    """
    Routes validation requests through a tiered execution flow.

    Tiers execute sequentially, but validators within a tier run in parallel.
    Supports dependencies, early termination, and user control over validators.
    """

    def __init__(
        self,
        agent_registry,
        config_loader: Optional[ConfigLoader] = None
    ):
        """
        Initialize the validator router.

        Args:
            agent_registry: The agent registry to look up validators
            config_loader: Optional config loader (uses default if not provided)
        """
        self.agent_registry = agent_registry
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("validation_flow")
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._build_dependency_graph()

    def _build_dependency_graph(self):
        """Build the dependency graph from config."""
        deps = self._config.get("dependencies", {})
        for validator_id, dep_list in deps.items():
            self._dependency_graph[validator_id] = set(dep_list)

    def _get_settings(self, profile: Optional[str] = None) -> Dict[str, Any]:
        """Get flow settings with profile overrides."""
        base_settings = self._config.get("settings", {})

        if profile:
            profile_config = self._config.get("profiles", {}).get(profile, {})
            profile_settings = profile_config.get("settings", {})
            return {**base_settings, **profile_settings}

        return base_settings

    def _get_enabled_validators(
        self,
        profile: Optional[str] = None,
        family: Optional[str] = None,
        user_selection: Optional[List[str]] = None
    ) -> Set[str]:
        """
        Get set of enabled validators based on profile, family, and user selection.

        Args:
            profile: Validation profile to use
            family: Product family for family-specific overrides
            user_selection: User-specified list of validators (overrides config)

        Returns:
            Set of enabled validator IDs
        """
        # Start with base validator config
        validators_config = self._config.get("validators", {})
        enabled = set()

        for val_id, val_config in validators_config.items():
            if val_config.get("enabled", True):
                enabled.add(val_id)

        # Apply profile overrides
        if profile:
            profile_config = self._config.get("profiles", {}).get(profile, {})
            profile_validators = profile_config.get("validators", {})
            for val_id, val_settings in profile_validators.items():
                if val_settings.get("enabled", True):
                    enabled.add(val_id)
                elif val_id in enabled:
                    enabled.discard(val_id)

        # Apply family overrides
        if family:
            family_config = self._config.get("family_overrides", {}).get(family, {})
            family_validators = family_config.get("validators", {})
            for val_id, val_settings in family_validators.items():
                if val_settings.get("enabled", True):
                    enabled.add(val_id)
                elif val_id in enabled:
                    enabled.discard(val_id)

        # User selection overrides everything
        if user_selection is not None:
            enabled = set(user_selection)

        return enabled

    def _get_tier_validators(self, tier_key: str) -> List[str]:
        """Get list of validators for a tier."""
        tiers = self._config.get("tiers", {})
        tier_config = tiers.get(tier_key, {})
        return tier_config.get("validators", [])

    def _get_tier_settings(self, tier_key: str) -> Dict[str, Any]:
        """Get settings for a specific tier."""
        tiers = self._config.get("tiers", {})
        tier_config = tiers.get(tier_key, {})
        return tier_config.get("settings", {})

    def _get_validator_agent_id(self, validator_id: str) -> Optional[str]:
        """Get agent ID for a validator."""
        validators_config = self._config.get("validators", {})
        val_config = validators_config.get(validator_id, {})
        return val_config.get("agent_id")

    def _check_dependencies_met(
        self,
        validator_id: str,
        completed_validators: Set[str]
    ) -> bool:
        """Check if all dependencies for a validator have been completed."""
        deps = self._dependency_graph.get(validator_id, set())
        return deps.issubset(completed_validators)

    def _count_issues_by_level(self, result: Dict[str, Any]) -> Dict[str, int]:
        """Count issues by severity level from a validation result."""
        counts = {"critical": 0, "error": 0, "warning": 0, "info": 0}

        issues = result.get("issues", [])
        for issue in issues:
            level = issue.get("level", "info").lower()
            if level in counts:
                counts[level] += 1

        return counts

    async def _execute_validator(
        self,
        validator_id: str,
        content: str,
        context: Dict[str, Any],
        timeout: float
    ) -> Dict[str, Any]:
        """
        Execute a single validator with timeout.

        Args:
            validator_id: ID of the validator to run
            content: Content to validate
            context: Validation context
            timeout: Timeout in seconds

        Returns:
            Validation result dict
        """
        agent_id = self._get_validator_agent_id(validator_id)
        if not agent_id:
            logger.warning(f"No agent ID configured for validator: {validator_id}")
            return {
                "confidence": 0.0,
                "issues": [{
                    "level": "error",
                    "category": "config_error",
                    "message": f"No agent ID configured for validator: {validator_id}"
                }],
                "error": "config_error"
            }

        agent = self.agent_registry.get_agent(agent_id)
        if not agent:
            logger.info(f"Validator agent not available: {agent_id}")
            return {
                "confidence": 0.0,
                "issues": [],
                "skipped": True,
                "reason": f"Agent {agent_id} not registered"
            }

        try:
            # Update context with validation type
            validation_context = {**context, "validation_type": validator_id}

            # Execute with timeout
            result = await asyncio.wait_for(
                agent.validate(content, validation_context),
                timeout=timeout
            )

            return {
                "confidence": result.confidence,
                "issues": [issue.to_dict() for issue in result.issues],
                "metrics": result.metrics,
                "agent_id": agent_id
            }

        except asyncio.TimeoutError:
            logger.warning(f"Validator {validator_id} timed out after {timeout}s")
            return {
                "confidence": 0.0,
                "issues": [{
                    "level": "warning",
                    "category": "timeout",
                    "message": f"Validator {validator_id} timed out after {timeout}s"
                }],
                "timeout": True
            }

        except Exception as e:
            logger.error(f"Error in validator {validator_id}: {e}", exc_info=True)
            return {
                "confidence": 0.0,
                "issues": [{
                    "level": "error",
                    "category": "validator_error",
                    "message": f"Error in validator {validator_id}: {str(e)}"
                }],
                "error": str(e)
            }

    async def _execute_tier(
        self,
        tier_key: str,
        tier_number: int,
        content: str,
        context: Dict[str, Any],
        enabled_validators: Set[str],
        completed_validators: Set[str],
        settings: Dict[str, Any]
    ) -> TierResult:
        """
        Execute a single tier of validators.

        Args:
            tier_key: Tier configuration key (e.g., "tier1")
            tier_number: Tier number (1, 2, or 3)
            content: Content to validate
            context: Validation context
            enabled_validators: Set of enabled validator IDs
            completed_validators: Set of already completed validator IDs
            settings: Flow settings

        Returns:
            TierResult with tier execution results
        """
        start_time = datetime.now()
        tier_result = TierResult(
            tier_name=tier_key,
            tier_number=tier_number
        )

        # Get tier config
        tiers = self._config.get("tiers", {})
        tier_config = tiers.get(tier_key, {})
        tier_validators = tier_config.get("validators", [])
        tier_settings = tier_config.get("settings", {})
        parallel = tier_config.get("parallel", True)

        # Merge settings
        effective_timeout = tier_settings.get("timeout", settings.get("validator_timeout", 60))
        respect_deps = tier_settings.get("respect_dependencies", True)

        # Filter to enabled validators
        validators_to_run = [v for v in tier_validators if v in enabled_validators]

        if not validators_to_run:
            logger.debug(f"No enabled validators for {tier_key}")
            return tier_result

        if parallel and not respect_deps:
            # Run all validators in parallel
            tasks = []
            for val_id in validators_to_run:
                tasks.append(self._execute_validator(val_id, content, context, effective_timeout))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for val_id, result in zip(validators_to_run, results):
                if isinstance(result, Exception):
                    tier_result.errors.append({
                        "validator": val_id,
                        "error": str(result)
                    })
                    tier_result.results[val_id] = {
                        "error": str(result),
                        "confidence": 0.0,
                        "issues": []
                    }
                else:
                    tier_result.results[val_id] = result
                    counts = self._count_issues_by_level(result)
                    tier_result.critical_count += counts["critical"]
                    tier_result.error_count += counts["error"]
                    tier_result.warning_count += counts["warning"]

                tier_result.validators_run.append(val_id)
                completed_validators.add(val_id)

        else:
            # Run with dependency ordering
            pending = set(validators_to_run)

            while pending:
                # Find validators whose dependencies are met
                ready = [
                    v for v in pending
                    if self._check_dependencies_met(v, completed_validators)
                ]

                if not ready:
                    # Deadlock or no validators ready
                    logger.warning(f"Cannot run remaining validators in {tier_key}: {pending}")
                    for val_id in pending:
                        tier_result.errors.append({
                            "validator": val_id,
                            "error": "Dependencies not met"
                        })
                    break

                if parallel:
                    # Run ready validators in parallel
                    tasks = []
                    for val_id in ready:
                        tasks.append(self._execute_validator(val_id, content, context, effective_timeout))

                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for val_id, result in zip(ready, results):
                        pending.discard(val_id)
                        if isinstance(result, Exception):
                            tier_result.errors.append({
                                "validator": val_id,
                                "error": str(result)
                            })
                            tier_result.results[val_id] = {
                                "error": str(result),
                                "confidence": 0.0,
                                "issues": []
                            }
                        else:
                            tier_result.results[val_id] = result
                            counts = self._count_issues_by_level(result)
                            tier_result.critical_count += counts["critical"]
                            tier_result.error_count += counts["error"]
                            tier_result.warning_count += counts["warning"]

                        tier_result.validators_run.append(val_id)
                        completed_validators.add(val_id)
                else:
                    # Run sequentially
                    for val_id in ready:
                        result = await self._execute_validator(val_id, content, context, effective_timeout)
                        pending.discard(val_id)
                        tier_result.results[val_id] = result
                        tier_result.validators_run.append(val_id)
                        completed_validators.add(val_id)

                        counts = self._count_issues_by_level(result)
                        tier_result.critical_count += counts["critical"]
                        tier_result.error_count += counts["error"]
                        tier_result.warning_count += counts["warning"]

                # Check for early termination
                max_critical = settings.get("max_critical_errors", 3)
                if settings.get("early_termination_on_critical", True):
                    if tier_result.critical_count >= max_critical:
                        tier_result.terminated_early = True
                        logger.warning(f"Early termination in {tier_key}: {tier_result.critical_count} critical errors")
                        break

        # Calculate duration
        tier_result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return tier_result

    async def execute(
        self,
        validation_types: Optional[List[str]] = None,
        content: str = "",
        context: Optional[Dict[str, Any]] = None,
        profile: Optional[str] = None,
        user_selection: Optional[List[str]] = None
    ) -> FlowResult:
        """
        Execute the full tiered validation flow.

        Args:
            validation_types: Optional list of validation types (for compatibility)
            content: Content to validate
            context: Validation context (file_path, family, etc.)
            profile: Validation profile to use
            user_selection: User-specified list of validators (overrides config)

        Returns:
            FlowResult with complete validation results
        """
        start_time = datetime.now()
        context = context or {}
        family = context.get("family")

        # Determine profile
        effective_profile = profile or self._config.get("profile", "default")

        # Apply family override for profile
        if family:
            family_config = self._config.get("family_overrides", {}).get(family, {})
            if "profile" in family_config:
                effective_profile = family_config["profile"]

        # Get settings
        settings = self._get_settings(effective_profile)

        # Get enabled validators
        # If validation_types provided, use as user selection for compatibility
        effective_selection = user_selection or validation_types
        enabled_validators = self._get_enabled_validators(
            profile=effective_profile,
            family=family,
            user_selection=effective_selection
        )

        logger.debug(f"Enabled validators: {enabled_validators}")

        flow_result = FlowResult()
        completed_validators: Set[str] = set()

        # Execute tiers in order
        tier_keys = ["tier1", "tier2", "tier3"]

        for tier_number, tier_key in enumerate(tier_keys, 1):
            tier_result = await self._execute_tier(
                tier_key=tier_key,
                tier_number=tier_number,
                content=content,
                context=context,
                enabled_validators=enabled_validators,
                completed_validators=completed_validators,
                settings=settings
            )

            flow_result.tiers_executed.append(tier_result)
            flow_result.total_critical += tier_result.critical_count
            flow_result.total_errors += tier_result.error_count
            flow_result.total_warnings += tier_result.warning_count

            # Merge validation results
            for val_id, val_result in tier_result.results.items():
                flow_result.validation_results[f"{val_id}_validation"] = val_result
                flow_result.routing_info[val_id] = (
                    "tiered_execution" if not val_result.get("skipped")
                    else "skipped"
                )

            # Check for early termination
            if tier_result.terminated_early:
                flow_result.terminated_early = True
                flow_result.termination_reason = f"Critical errors in {tier_key}"
                break

            # Check total critical errors
            max_critical = settings.get("max_critical_errors", 3)
            if settings.get("early_termination_on_critical", True):
                if flow_result.total_critical >= max_critical:
                    flow_result.terminated_early = True
                    flow_result.termination_reason = f"Total critical errors ({flow_result.total_critical}) exceeded max ({max_critical})"
                    break

        # Calculate total duration
        flow_result.total_duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return flow_result

    def get_available_validators(self) -> List[Dict[str, Any]]:
        """
        Get list of all configured validators with availability status.

        Returns:
            List of validator info dicts
        """
        validators_config = self._config.get("validators", {})
        result = []

        for val_id, val_config in validators_config.items():
            agent_id = val_config.get("agent_id")
            agent = self.agent_registry.get_agent(agent_id) if agent_id else None

            result.append({
                "id": val_id,
                "agent_id": agent_id,
                "description": val_config.get("description", ""),
                "category": val_config.get("category", "standard"),
                "tier": val_config.get("tier", 0),
                "enabled": val_config.get("enabled", True),
                "available": agent is not None,
                "dependencies": list(self._dependency_graph.get(val_id, set()))
            })

        # Sort by tier, then by ID
        result.sort(key=lambda x: (x["tier"], x["id"]))

        return result

    def get_tier_info(self) -> List[Dict[str, Any]]:
        """
        Get information about configured tiers.

        Returns:
            List of tier info dicts
        """
        tiers_config = self._config.get("tiers", {})
        result = []

        for tier_key in ["tier1", "tier2", "tier3"]:
            tier_config = tiers_config.get(tier_key, {})
            if tier_config:
                result.append({
                    "key": tier_key,
                    "number": int(tier_key[-1]),
                    "name": tier_config.get("name", tier_key),
                    "description": tier_config.get("description", ""),
                    "parallel": tier_config.get("parallel", True),
                    "validators": tier_config.get("validators", []),
                    "settings": tier_config.get("settings", {})
                })

        return result

    def reload_config(self):
        """Reload configuration from disk."""
        self._config = self._config_loader.load("validation_flow")
        self._build_dependency_graph()
        logger.info("ValidatorRouter configuration reloaded")
