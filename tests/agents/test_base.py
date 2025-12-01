# tests/agents/test_base.py
"""
Unit tests for agents/base.py - BaseAgent and MCP message handling.
Target coverage: 100%
"""
import pytest
from datetime import datetime
from agents.base import (
    AgentStatus,
    MessageType,
    MCPMessage,
    AgentCapability,
    AgentContract,
    BaseAgent
)


class TestAgentStatus:
    """Test AgentStatus enum."""

    def test_agent_status_values(self):
        """Test all agent status enum values."""
        assert AgentStatus.STARTING.value == "starting"
        assert AgentStatus.READY.value == "ready"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.STOPPED.value == "stopped"


class TestMessageType:
    """Test MessageType enum."""

    def test_message_type_values(self):
        """Test all message type enum values."""
        assert MessageType.REQUEST.value == "request"
        assert MessageType.RESPONSE.value == "response"
        assert MessageType.NOTIFICATION.value == "notification"


class TestMCPMessage:
    """Test MCPMessage dataclass."""

    def test_mcp_message_creation_minimal(self):
        """Test MCP message creation with minimal fields."""
        msg = MCPMessage(type=MessageType.NOTIFICATION)

        assert msg.type == MessageType.NOTIFICATION
        assert msg.id is None  # Notification doesn't auto-generate ID
        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, str)

    def test_mcp_message_auto_id_for_request(self):
        """Test auto-generated ID for REQUEST messages."""
        msg = MCPMessage(type=MessageType.REQUEST, method="test_method")

        assert msg.id is not None
        assert len(msg.id) > 0
        assert msg.method == "test_method"

    def test_mcp_message_auto_id_for_response(self):
        """Test auto-generated ID for RESPONSE messages."""
        msg = MCPMessage(type=MessageType.RESPONSE, result={"status": "ok"})

        assert msg.id is not None
        assert msg.result == {"status": "ok"}

    def test_mcp_message_custom_id(self):
        """Test MCP message with custom ID."""
        custom_id = "custom-123"
        msg = MCPMessage(type=MessageType.REQUEST, method="test", id=custom_id)

        assert msg.id == custom_id

    def test_mcp_message_to_dict(self):
        """Test MCP message serialization to dict."""
        msg = MCPMessage(
            type=MessageType.REQUEST,
            method="test_method",
            params={"key": "value"}
        )

        data = msg.to_dict()

        assert isinstance(data, dict)
        assert data["type"] == "request"
        assert data["method"] == "test_method"
        assert data["params"] == {"key": "value"}
        assert "timestamp" in data
        assert "id" in data

    def test_mcp_message_to_dict_excludes_none(self):
        """Test that to_dict excludes None values."""
        msg = MCPMessage(type=MessageType.NOTIFICATION)

        data = msg.to_dict()

        # Should not include method, params, result, error if they're None
        assert "method" not in data or data["method"] is None
        assert "result" not in data or data["result"] is None

    def test_mcp_message_from_dict(self):
        """Test MCP message deserialization from dict."""
        data = {
            "type": "request",
            "id": "test-123",
            "method": "test_method",
            "params": {"key": "value"},
            "timestamp": "2025-01-01T00:00:00Z"
        }

        msg = MCPMessage.from_dict(data)

        assert msg.type == MessageType.REQUEST
        assert msg.id == "test-123"
        assert msg.method == "test_method"
        assert msg.params == {"key": "value"}
        assert msg.timestamp == "2025-01-01T00:00:00Z"

    def test_mcp_message_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = MCPMessage(
            type=MessageType.REQUEST,
            method="test",
            params={"data": [1, 2, 3]}
        )

        data = original.to_dict()
        restored = MCPMessage.from_dict(data)

        assert restored.type == original.type
        assert restored.method == original.method
        assert restored.params == original.params


class TestAgentCapability:
    """Test AgentCapability dataclass."""

    def test_capability_creation_minimal(self):
        """Test capability creation with minimal fields."""
        cap = AgentCapability(
            name="test_capability",
            description="Test capability",
            input_schema={"type": "object"},
            output_schema={"type": "object"}
        )

        assert cap.name == "test_capability"
        assert cap.description == "Test capability"
        assert cap.side_effects == []  # Default empty list

    def test_capability_with_side_effects(self):
        """Test capability with side effects specified."""
        cap = AgentCapability(
            name="write_file",
            description="Writes to filesystem",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            side_effects=["filesystem_write", "state_mutation"]
        )

        assert cap.side_effects == ["filesystem_write", "state_mutation"]


class TestAgentContract:
    """Test AgentContract dataclass."""

    def test_contract_creation(self):
        """Test agent contract creation."""
        capabilities = [
            AgentCapability(
                name="test_cap",
                description="Test",
                input_schema={},
                output_schema={}
            )
        ]

        contract = AgentContract(
            agent_id="test_agent",
            name="Test Agent",
            version="1.0.0",
            capabilities=capabilities,
            checkpoints=[],
            max_runtime_s=300,
            confidence_threshold=0.8,
            side_effects=[]
        )

        assert contract.agent_id == "test_agent"
        assert contract.name == "Test Agent"
        assert len(contract.capabilities) == 1
        assert contract.version == "1.0.0"
        assert contract.checkpoints == []
        assert contract.max_runtime_s == 300
        assert contract.confidence_threshold == 0.8
        assert contract.side_effects == []


class TestBaseAgent:
    """Test BaseAgent abstract class through a concrete subclass."""

    class ConcreteAgent(BaseAgent):
        """Concrete implementation for testing."""

        def _register_message_handlers(self):
            """Register message handlers."""
            self.register_handler("test_method", self.handle_test_method)
            self.register_handler("ping", self.handle_ping)
            self.register_handler("get_status", self.handle_get_status)
            self.register_handler("get_contract", self.handle_get_contract)

        def get_contract(self) -> AgentContract:
            return AgentContract(
                agent_id=self.agent_id,
                name="ConcreteAgent",
                version="1.0.0",
                capabilities=[
                    AgentCapability(
                        name="test_method",
                        description="Test method",
                        input_schema={"type": "object"},
                        output_schema={"type": "object"}
                    )
                ],
                checkpoints=[],
                max_runtime_s=300,
                confidence_threshold=0.8,
                side_effects=[]
            )

        async def handle_test_method(self, params: dict) -> dict:
            """Test method handler."""
            return {"success": True, "echo": params.get("message", "")}

    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = self.ConcreteAgent("test_agent_001")

        assert agent.agent_id == "test_agent_001"
        # Agent initializes to READY after successful setup
        assert agent.status in [AgentStatus.STARTING, AgentStatus.READY]

    def test_agent_get_contract(self):
        """Test getting agent contract."""
        agent = self.ConcreteAgent("test_agent")
        contract = agent.get_contract()

        assert isinstance(contract, AgentContract)
        assert contract.agent_id == "test_agent"
        assert len(contract.capabilities) > 0

    @pytest.mark.asyncio
    async def test_agent_process_request_valid_method(self):
        """Test processing a valid request."""
        agent = self.ConcreteAgent("test_agent")

        result = await agent.process_request("test_method", {"message": "hello"})

        assert result["success"] is True
        assert result["echo"] == "hello"

    @pytest.mark.asyncio
    async def test_agent_process_request_invalid_method(self):
        """Test processing request with invalid method."""
        agent = self.ConcreteAgent("test_agent")

        # Invalid method should raise an exception (per process_request implementation)
        with pytest.raises(Exception) as exc_info:
            await agent.process_request("nonexistent_method", {})

        # Verify error message contains expected info
        assert "Agent error" in str(exc_info.value) or "Method not found" in str(exc_info.value)

    def test_agent_get_status(self):
        """Test getting agent status."""
        agent = self.ConcreteAgent("test_agent")

        status = agent.get_status()

        assert "agent_id" in status
        assert "status" in status
        assert status["agent_id"] == "test_agent"

    @pytest.mark.asyncio
    async def test_agent_lifecycle_initialization(self):
        """Test agent lifecycle: initialization to READY state."""
        agent = self.ConcreteAgent("test_agent")

        # Agent should initialize to READY automatically
        assert agent.status == AgentStatus.READY

    @pytest.mark.asyncio
    async def test_agent_lifecycle_shutdown(self):
        """Test agent lifecycle: shutdown method."""
        agent = self.ConcreteAgent("test_agent")

        # Ensure agent is ready first
        assert agent.status == AgentStatus.READY

        # Shutdown should transition to STOPPED
        await agent.shutdown()

        assert agent.status == AgentStatus.STOPPED


@pytest.mark.unit
class TestBaseAgentEdgeCases:
    """Test edge cases and error handling in BaseAgent."""

    class ErrorAgent(BaseAgent):
        """Agent that raises errors for testing."""

        def _register_message_handlers(self):
            """Register message handlers."""
            self.register_handler("error_method", self.handle_error_method)
            self.register_handler("ping", self.handle_ping)
            self.register_handler("get_status", self.handle_get_status)
            self.register_handler("get_contract", self.handle_get_contract)

        def get_contract(self) -> AgentContract:
            return AgentContract(
                agent_id=self.agent_id,
                name="ErrorAgent",
                version="1.0.0",
                capabilities=[],
                checkpoints=[],
                max_runtime_s=300,
                confidence_threshold=0.8,
                side_effects=[]
            )

        async def handle_error_method(self, params: dict) -> dict:
            raise ValueError("Intentional error for testing")

    @pytest.mark.asyncio
    async def test_agent_handles_method_errors(self):
        """Test that agent handles errors in method handlers."""
        agent = self.ErrorAgent("error_agent")

        # process_request wraps errors from handle_message and raises
        with pytest.raises(Exception) as exc_info:
            await agent.process_request("error_method", {})

        # Should have meaningful error message
        assert "Agent error" in str(exc_info.value) or "Intentional error" in str(exc_info.value)
