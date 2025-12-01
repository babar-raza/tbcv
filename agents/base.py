# file: tbcv\agents\base.py
# Location: scripts/tbcv/agents/base.py
# Base agent class implementing MCP (Model Context Protocol) framework.
# Provides common functionality for all TBCV agents including message handling,
# contract management, caching integration, and performance monitoring.
#
# NOTE (import model):
# - We use ABSOLUTE imports (core.*, agents.*) so this module can be executed
#   when `agents/` and `core/` directories are added to sys.path by run_tests.py.
# - Relative imports (..core.*) fail when files are run outside a package context.

import uuid
import json
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict

from core.config import get_settings 
from core.logging import get_logger, LoggerMixin, PerformanceLogger
from core.cache import cache_manager


class AgentStatus(Enum):
    """Lifecycle states for an agent; used by health checks and orchestrator."""
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class MessageType(Enum):
    """MCP message types recommended for inter-agent RPC."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


@dataclass
class MCPMessage:
    """
    Standardized MCP (Model Context Protocol) message.
    - `type`: request/response/notification
    - `id`: unique id for request/response pairing (auto for req/resp)
    - `method`: operation name (for REQUEST)
    - `params`: input payload
    - `result`: output payload (for RESPONSE)
    - `error`: error payload (for RESPONSE failures)
    - `timestamp`: ISO-8601 string (auto-filled)
    """
    type: MessageType
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Ensure timestamp & id exist for traceability and pairing."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat() + 'Z'
        if self.id is None and self.type in [MessageType.REQUEST, MessageType.RESPONSE]:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the message to a plain dict (safe for JSON)."""
        data = asdict(self)
        data['type'] = data['type'].value
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Deserialize from dict, normalizing the enum field."""
        data['type'] = MessageType(data['type'])
        return cls(**data)


@dataclass
class AgentCapability:
    """
    Defines a single callable capability of an agent.
    Include input/output JSON Schemas and declare side effects.
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    side_effects: List[str] = None

    def __post_init__(self):
        if self.side_effects is None:
            self.side_effects = []


@dataclass
class AgentContract:
    """
    Full agent contract: identity, capabilities, checkpoints, limits.
    Used by the orchestrator for discovery and planning.
    """
    agent_id: str
    name: str
    version: str
    capabilities: List[AgentCapability]
    checkpoints: List[str]
    max_runtime_s: int
    confidence_threshold: float
    side_effects: List[str]
    dependencies: List[str] = None
    resource_limits: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.resource_limits is None:
            self.resource_limits = {
                "max_memory_mb": 512,
                "max_cpu_percent": 80,
                "max_concurrent": 5
            }

    def to_dict(self) -> Dict[str, Any]:
        """Contract as a dict for API responses or logs."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "checkpoints": self.checkpoints,
            "max_runtime_s": self.max_runtime_s,
            "confidence_threshold": self.confidence_threshold,
            "side_effects": self.side_effects,
            "dependencies": self.dependencies,
            "resource_limits": self.resource_limits
        }


class BaseAgent(LoggerMixin, ABC):
    """
    Abstract base for all TBCV agents (MCP-compliant).
    Provides:
      - Message routing (method -> async handler)
      - Contract retrieval
      - Stats tracking (avg latency, errors)
      - Cache helpers (get/put/clear)
      - Checkpoints (create/restore stubs)
      - Logging context via LoggerMixin
    """

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__()

        # Identity & state
        self.agent_id = agent_id or f"{self.__class__.__name__.lower()}_{uuid.uuid4().hex[:8]}"
        self.status = AgentStatus.STARTING
        self.settings = get_settings()
        self.last_heartbeat = datetime.now(timezone.utc)

        # Basic statistics for monitoring/SLAs
        self.statistics = {
            "requests_processed": 0,
            "average_response_time_ms": 0.0,
            "error_count": 0,
            "cache_hit_rate": 0.0,   # hook up to cache_manager metrics if desired
            "total_response_time_ms": 0
        }

        # Request/handler registry
        self.message_handlers = {}  # method -> async function
        self.pending_requests = {}  # request id -> future (optional)

        # Ensure logs carry an agent_id for correlation
        self.set_log_context(agent_id=self.agent_id)

        # Allow subclasses to register handlers & validate config
        self._initialize()

    def _initialize(self):
        """Lifecycle hook: register handlers and validate config."""
        try:
            self._register_message_handlers()
            self._validate_configuration()
            self.status = AgentStatus.READY
            self.logger.info("Agent initialized successfully")
        except Exception as e:
            self.status = AgentStatus.ERROR
            # Avoid passing unexpected kwargs to stdlib logger
            self.logger.exception("Agent initialization failed")
            raise

    @abstractmethod
    def _register_message_handlers(self):
        """Subclasses MUST map RPC method names to async handlers here."""
        ...

    @abstractmethod
    def get_contract(self) -> AgentContract:
        """Subclasses MUST return their AgentContract."""
        ...

    def _validate_configuration(self):
        """Optional: subclasses may raise on invalid settings."""
        pass

    # ---------- Message routing ----------

    def register_handler(self, method: str, handler_func):
        """Register an async handler for an MCP method name."""
        self.message_handlers[method] = handler_func
        self.logger.debug("Handler registered", method=method)

    async def handle_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """
        Route an incoming MCP message to its handler.
        Returns a RESPONSE message for REQUESTs; None for NOTIFICATIONs.
        """
        if self.status != AgentStatus.READY:
            return MCPMessage(
                type=MessageType.RESPONSE,
                id=message.id,
                error={"code": -32603, "message": f"Agent not ready (status: {self.status.value})"}
            )

        with PerformanceLogger(self.logger, f"handle_message_{message.method}") as perf:
            try:
                self.status = AgentStatus.BUSY
                start_time = datetime.now(timezone.utc)

                if message.method in self.message_handlers:
                    handler = self.message_handlers[message.method]
                    result = await handler(message.params or {})
                    response = MCPMessage(type=MessageType.RESPONSE, id=message.id, result=result)

                    # Stats update
                    end_time = datetime.now(timezone.utc)
                    rt_ms = (end_time - start_time).total_seconds() * 1000
                    self._update_statistics(rt_ms, success=True)
                    perf.add_context(success=True, response_time_ms=rt_ms)
                else:
                    response = MCPMessage(
                        type=MessageType.RESPONSE,
                        id=message.id,
                        error={"code": -32601, "message": f"Method not found: {message.method}"}
                    )
                    self._update_statistics(0, success=False)
                    perf.add_context(success=False, error="method_not_found")

                self.status = AgentStatus.READY
                return response

            except Exception as e:
                self.status = AgentStatus.READY
                self.logger.exception("Message handling failed")
                self._update_statistics(0, success=False)
                perf.add_context(success=False, error=str(e))
                return MCPMessage(
                    type=MessageType.RESPONSE,
                    id=message.id,
                    error={"code": -32603, "message": f"Internal error: {str(e)}"}
                )

    def _update_statistics(self, response_time_ms: float, success: bool):
        """Lightweight rolling stats; suitable for health endpoints."""
        self.statistics["requests_processed"] += 1
        if success:
            self.statistics["total_response_time_ms"] += response_time_ms
            self.statistics["average_response_time_ms"] = (
                self.statistics["total_response_time_ms"] / self.statistics["requests_processed"]
            )
        else:
            self.statistics["error_count"] += 1

    # ---------- Convenience handlers ----------

    async def handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Health probe hook; returns a quick pong with timestamps."""
        self.heartbeat()
        return {"pong": True, "timestamp": datetime.now(timezone.utc).isoformat(), "agent_id": self.agent_id}

    async def handle_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return a snapshot of agent status + statistics."""
        return self.get_status()

    async def handle_get_contract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Expose the agent contract for discovery endpoints."""
        return self.get_contract().to_dict()

    # ---------- Cache helpers ----------

    def get_cached_result(self, method: str, input_data: Any) -> Optional[Any]:
        """Look up a cached result for (agent_id, method, input)."""
        return cache_manager.get(self.agent_id, method, input_data)

    def cache_result(self, method: str, input_data: Any, result: Any, ttl_seconds: Optional[int] = None):
        """Persist a result to cache for (agent_id, method, input)."""
        cache_manager.put(self.agent_id, method, input_data, result, ttl_seconds)

    def clear_cache(self):
        """Clear all cache entries owned by this agent."""
        cache_manager.clear_agent_cache(self.agent_id)

    # ---------- Checkpoints ----------

    def create_checkpoint(self, name: str, data: Dict[str, Any], workflow_id: Optional[str] = None) -> str:
        """
        Create a named checkpoint snapshot for resumable operations.
        Persists checkpoint data to the database for recovery.

        Args:
            name: Human-readable checkpoint name
            data: State data to save (will be pickled)
            workflow_id: Optional workflow ID to associate with checkpoint

        Returns:
            checkpoint_id: UUID of created checkpoint
        """
        import pickle
        from core.database import Checkpoint, db_manager

        checkpoint_id = str(uuid.uuid4())

        try:
            # Serialize the state data
            state_data = pickle.dumps(data)

            # Use provided workflow_id or create agent-specific sentinel ID
            if not workflow_id:
                workflow_id = f"agent_{self.agent_id}_{checkpoint_id[:8]}"

            # Calculate validation hash for integrity checking
            import hashlib
            validation_hash = hashlib.md5(state_data).hexdigest()

            # Store in database
            with db_manager.get_session() as session:
                checkpoint = Checkpoint(
                    id=checkpoint_id,
                    workflow_id=workflow_id,
                    name=name,
                    step_number=0,
                    state_data=state_data,
                    validation_hash=validation_hash,
                    can_resume_from=True
                )
                session.add(checkpoint)
                session.commit()

            self.logger.info("Checkpoint created and persisted",
                           checkpoint_id=checkpoint_id,
                           name=name,
                           size_bytes=len(state_data))
            return checkpoint_id

        except Exception as e:
            self.logger.error("Failed to create checkpoint",
                            checkpoint_id=checkpoint_id,
                            name=name,
                            error=str(e))
            raise

    def restore_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Restore previously saved state from a checkpoint.

        Args:
            checkpoint_id: UUID of the checkpoint to restore

        Returns:
            data: The restored state data dictionary

        Raises:
            ValueError: If checkpoint not found or validation fails
        """
        import pickle
        import hashlib
        from core.database import Checkpoint, db_manager

        try:
            with db_manager.get_session() as session:
                checkpoint = session.query(Checkpoint).filter(
                    Checkpoint.id == checkpoint_id
                ).first()

                if not checkpoint:
                    raise ValueError(f"Checkpoint {checkpoint_id} not found")

                if not checkpoint.can_resume_from:
                    raise ValueError(f"Checkpoint {checkpoint_id} is not resumable")

                # Validate integrity
                state_data = checkpoint.state_data
                if checkpoint.validation_hash:
                    actual_hash = hashlib.md5(state_data).hexdigest()
                    if actual_hash != checkpoint.validation_hash:
                        raise ValueError(f"Checkpoint {checkpoint_id} failed integrity check")

                # Deserialize state
                restored_data = pickle.loads(state_data)

                self.logger.info("Checkpoint restored",
                               checkpoint_id=checkpoint_id,
                               name=checkpoint.name)
                return restored_data

        except Exception as e:
            self.logger.error("Failed to restore checkpoint",
                            checkpoint_id=checkpoint_id,
                            error=str(e))
            raise

    # ---------- Misc utilities ----------

    def validate_input(self, input_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate a dict against a JSON Schema (best-effort; warns on failure)."""
        try:
            import jsonschema
            jsonschema.validate(input_data, schema)
            return True
        except Exception as e:
            self.logger.warning("Input validation failed", error=str(e))
            return False

    def calculate_confidence(self, factors: Dict[str, float], weights: Dict[str, float]) -> float:
        """Weighted confidence aggregator in range [0, 1]."""
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(factors.get(f, 0.0) * w for f, w in weights.items())
        return min(1.0, max(0.0, weighted_sum / total_weight))

    async def process_request(self, method: str, params: Dict[str, Any]) -> Any:
        """
        Internal RPC helper used by the orchestrator:
          - Wraps `handle_message` with a REQUEST envelope.
          - Raises on MCP error shape.
        """
        message = MCPMessage(type=MessageType.REQUEST, method=method, params=params)
        response = await self.handle_message(message)
        if response.error:
            raise Exception(f"Agent error: {response.error['message']}")
        return response.result

    def heartbeat(self):
        """Update internal heartbeat to 'now'; used by /status endpoints."""
        self.last_heartbeat = datetime.now(timezone.utc)

    def get_status(self) -> Dict[str, Any]:
        """Comprehensive agent status for debugging and dashboards."""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "statistics": self.statistics.copy(),
        }

    async def shutdown(self):
        """Graceful shutdown hook; orchestrator may call on teardown."""
        self.status = AgentStatus.STOPPED
        self.logger.info("Agent shutdown completed")


class AgentRegistry:
    """
    Process-wide registry of agents and their contracts.
    Used by the orchestrator and API for discovery/broadcasts.
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}     # id -> BaseAgent
        self.contracts: Dict[str, AgentContract] = {}  # id -> AgentContract
        self.logger = get_logger("agent_registry")

    def register_agent(self, agent: BaseAgent):
        """Make an agent discoverable and cache its contract."""
        self.agents[agent.agent_id] = agent
        self.contracts[agent.agent_id] = agent.get_contract()
        self.logger.info("Agent registered", agent_id=agent.agent_id, agent_type=agent.__class__.__name__)

    def unregister_agent(self, agent_id: str):
        """Remove agent (e.g., on shutdown)."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            if agent_id in self.contracts:
                del self.contracts[agent_id]
            self.logger.info("Agent unregistered", agent_id=agent_id)

    def clear(self):
        """Clear all registered agents."""
        self.agents.clear()
        self.contracts.clear()
        self.logger.info("Agent registry cleared")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Lookup an agent instance by id."""
        return self.agents.get(agent_id)

    def get_contract(self, agent_id: str) -> Optional[AgentContract]:
        """Lookup the contract for a given agent id."""
        return self.contracts.get(agent_id)

    def list_agents(self) -> Dict[str, BaseAgent]:
        """
        Return a mapping of registered agents (id -> instance).
        This matches API usage expecting `.items()`.
        """
        return dict(self.agents)

    def summarize_agents(self) -> List[Dict[str, Any]]:
        """
        Legacy summary list shape (kept for compatibility with any callers
        that expected the previous list-of-dicts return from list_agents()).
        """
        summary: List[Dict[str, Any]] = []
        for agent_id, agent in self.agents.items():
            contract = self.contracts.get(agent_id)
            summary.append({
                "agent_id": agent_id,
                "status": agent.status.value,
                "contract": contract.to_dict() if contract else None,
            })
        return summary

    def reload_agent(self, agent_id: str) -> None:
        """
        Reload a specific agent.

        Args:
            agent_id: Agent ID to reload

        Raises:
            ValueError: If agent not found
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: {agent_id}")

        agent = self.agents[agent_id]

        # Clear agent's cache
        cache_manager.clear_agent_cache(agent_id)

        # Update contract
        self.contracts[agent_id] = agent.get_contract()

        self.logger.info("Agent reloaded", agent_id=agent_id)

    async def broadcast_message(self, message: MCPMessage, target_agents: Optional[List[str]] = None) -> Dict[str, MCPMessage]:
        """
        Send the same MCP message to multiple agents; collect responses.
        Useful for scatter/gather patterns.
        """
        targets = target_agents or list(self.agents.keys())
        responses: Dict[str, MCPMessage] = {}
        for agent_id in targets:
            if agent_id in self.agents:
                try:
                    responses[agent_id] = await self.agents[agent_id].handle_message(message)
                except Exception as e:
                    self.logger.error("Broadcast failed for agent", agent_id=agent_id, error=str(e))
                    responses[agent_id] = MCPMessage(
                        type=MessageType.RESPONSE,
                        error={"code": -32603, "message": str(e)}
                    )
        return responses

    def list_validators(self) -> List[Dict[str, Any]]:
        """
        Get list of available validators.

        Returns:
            List of validator information dictionaries
        """
        validators = []
        for agent_id, agent in self.agents.items():
            contract = self.contracts.get(agent_id)
            if contract and hasattr(contract, 'validator_type'):
                validators.append({
                    "id": agent_id,
                    "type": getattr(contract, 'validator_type', 'unknown'),
                    "name": getattr(contract, 'name', agent_id),
                    "description": getattr(contract, 'description', ''),
                    "status": agent.status.value if hasattr(agent.status, 'value') else str(agent.status)
                })
            else:
                # Include all agents as potential validators
                validators.append({
                    "id": agent_id,
                    "type": "generic",
                    "name": agent_id,
                    "description": f"Agent {agent_id}",
                    "status": agent.status.value if hasattr(agent.status, 'value') else str(agent.status)
                })
        return validators


# Global registry shared process-wide
agent_registry = AgentRegistry()
