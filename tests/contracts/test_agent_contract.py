"""
Contract tests for agents.base.BaseAgent.

These tests verify that the BaseAgent public API remains stable.
"""

import pytest
from agents.base import (
    BaseAgent, AgentStatus, MessageType, MCPMessage,
    AgentCapability, AgentContract, AgentRegistry, agent_registry
)


class TestBaseAgentContract:
    """Verify BaseAgent has all required public methods."""

    def test_base_agent_interface(self):
        """BaseAgent must have all required public methods."""
        required_methods = [
            # Core methods
            "get_contract",
            "handle_message",
            "register_handler",

            # Built-in handlers
            "handle_ping",
            "handle_get_status",
            "handle_get_contract",

            # Cache methods
            "get_cached_result",
            "cache_result",
            "clear_cache",

            # Checkpoint methods
            "create_checkpoint",
            "restore_checkpoint",

            # Utilities
            "validate_input",
            "calculate_confidence",
            "process_request",
            "heartbeat",
            "get_status",
            "shutdown",
        ]

        for method in required_methods:
            assert hasattr(BaseAgent, method), \
                f"BaseAgent missing required method: {method}"
            # Methods can be regular or abstract, just check they exist
            assert method in dir(BaseAgent), \
                f"BaseAgent.{method} not found in class"

    def test_base_agent_has_abstract_methods(self):
        """BaseAgent must declare abstract methods for subclasses."""
        import inspect

        # BaseAgent is abstract and should have these abstract methods
        abstract_methods = {
            '_register_message_handlers',
            'get_contract',
        }

        # Get all abstract methods
        actual_abstract = set()
        for name, method in inspect.getmembers(BaseAgent):
            if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                actual_abstract.add(name)

        for method in abstract_methods:
            assert method in actual_abstract, \
                f"BaseAgent.{method} should be abstract"

    def test_base_agent_attributes_exist(self):
        """BaseAgent instances must have required attributes."""
        # Can't instantiate abstract class, but we can check class attributes
        required_attrs = [
            'agent_id',
            'status',
            'settings',
            'statistics',
            'message_handlers',
        ]

        # These should be initialized in __init__
        # We verify by checking they're mentioned in the class
        import inspect
        source = inspect.getsource(BaseAgent.__init__)

        for attr in required_attrs:
            assert f"self.{attr}" in source, \
                f"BaseAgent.__init__ should initialize self.{attr}"


class TestAgentEnums:
    """Verify all required enums exist."""

    def test_agent_status_enum_exists(self):
        """AgentStatus enum must exist with required values."""
        required_values = ['STARTING', 'READY', 'BUSY', 'ERROR', 'STOPPED']

        for value in required_values:
            assert hasattr(AgentStatus, value), \
                f"AgentStatus missing value: {value}"

    def test_message_type_enum_exists(self):
        """MessageType enum must exist with required values."""
        required_values = ['REQUEST', 'RESPONSE', 'NOTIFICATION']

        for value in required_values:
            assert hasattr(MessageType, value), \
                f"MessageType missing value: {value}"


class TestMCPMessageContract:
    """Verify MCPMessage dataclass contract."""

    def test_mcp_message_has_required_fields(self):
        """MCPMessage must have all required fields."""
        import inspect
        from dataclasses import fields

        required_fields = {
            'type', 'id', 'method', 'params',
            'result', 'error', 'timestamp'
        }

        actual_fields = {f.name for f in fields(MCPMessage)}

        for field in required_fields:
            assert field in actual_fields, \
                f"MCPMessage missing field: {field}"

    def test_mcp_message_to_dict_exists(self):
        """MCPMessage must have to_dict() method."""
        assert hasattr(MCPMessage, 'to_dict')
        assert callable(MCPMessage.to_dict)

    def test_mcp_message_from_dict_exists(self):
        """MCPMessage must have from_dict() class method."""
        assert hasattr(MCPMessage, 'from_dict')
        assert callable(MCPMessage.from_dict)

    def test_mcp_message_can_be_created(self):
        """MCPMessage must be instantiable."""
        msg = MCPMessage(type=MessageType.REQUEST, method="test")
        assert msg is not None
        assert msg.type == MessageType.REQUEST
        assert msg.method == "test"
        assert msg.timestamp is not None
        assert msg.id is not None

    def test_mcp_message_to_dict_works(self):
        """to_dict() must return a serializable dict."""
        msg = MCPMessage(type=MessageType.REQUEST, method="test", params={"key": "value"})
        result = msg.to_dict()

        assert isinstance(result, dict)
        assert result['type'] == 'request'
        assert result['method'] == 'test'
        assert result['params'] == {"key": "value"}

    def test_mcp_message_from_dict_works(self):
        """from_dict() must reconstruct a message."""
        data = {
            'type': 'request',
            'method': 'test',
            'params': {'key': 'value'}
        }
        msg = MCPMessage.from_dict(data)

        assert isinstance(msg, MCPMessage)
        assert msg.type == MessageType.REQUEST
        assert msg.method == 'test'
        assert msg.params == {'key': 'value'}


class TestAgentCapabilityContract:
    """Verify AgentCapability dataclass contract."""

    def test_agent_capability_has_required_fields(self):
        """AgentCapability must have all required fields."""
        from dataclasses import fields

        required_fields = {
            'name', 'description', 'input_schema',
            'output_schema', 'side_effects'
        }

        actual_fields = {f.name for f in fields(AgentCapability)}

        for field in required_fields:
            assert field in actual_fields, \
                f"AgentCapability missing field: {field}"

    def test_agent_capability_can_be_created(self):
        """AgentCapability must be instantiable."""
        cap = AgentCapability(
            name="test_cap",
            description="Test capability",
            input_schema={"type": "object"},
            output_schema={"type": "object"}
        )
        assert cap is not None
        assert cap.name == "test_cap"
        assert cap.side_effects == []  # Default value


class TestAgentContractContract:
    """Verify AgentContract dataclass contract."""

    def test_agent_contract_has_required_fields(self):
        """AgentContract must have all required fields."""
        from dataclasses import fields

        required_fields = {
            'agent_id', 'name', 'version', 'capabilities',
            'checkpoints', 'max_runtime_s', 'confidence_threshold',
            'side_effects', 'dependencies', 'resource_limits'
        }

        actual_fields = {f.name for f in fields(AgentContract)}

        for field in required_fields:
            assert field in actual_fields, \
                f"AgentContract missing field: {field}"

    def test_agent_contract_to_dict_exists(self):
        """AgentContract must have to_dict() method."""
        assert hasattr(AgentContract, 'to_dict')
        assert callable(AgentContract.to_dict)

    def test_agent_contract_can_be_created(self):
        """AgentContract must be instantiable."""
        contract = AgentContract(
            agent_id="test_agent",
            name="Test Agent",
            version="1.0.0",
            capabilities=[],
            checkpoints=["start", "end"],
            max_runtime_s=300,
            confidence_threshold=0.8,
            side_effects=[]
        )
        assert contract is not None
        assert contract.agent_id == "test_agent"
        assert contract.dependencies == []  # Default
        assert isinstance(contract.resource_limits, dict)

    def test_agent_contract_to_dict_works(self):
        """to_dict() must return a serializable dict."""
        cap = AgentCapability(
            name="test",
            description="Test",
            input_schema={},
            output_schema={}
        )
        contract = AgentContract(
            agent_id="test",
            name="Test",
            version="1.0",
            capabilities=[cap],
            checkpoints=[],
            max_runtime_s=100,
            confidence_threshold=0.5,
            side_effects=[]
        )
        result = contract.to_dict()

        assert isinstance(result, dict)
        assert result['agent_id'] == 'test'
        assert result['name'] == 'Test'
        assert isinstance(result['capabilities'], list)


class TestAgentRegistryContract:
    """Verify AgentRegistry has all required public methods."""

    def test_agent_registry_interface(self):
        """AgentRegistry must have all required public methods."""
        required_methods = [
            "register_agent",
            "unregister_agent",
            "clear",
            "get_agent",
            "get_contract",
            "list_agents",
            "summarize_agents",
            "broadcast_message",
        ]

        for method in required_methods:
            assert hasattr(AgentRegistry, method), \
                f"AgentRegistry missing required method: {method}"
            assert callable(getattr(AgentRegistry, method)), \
                f"AgentRegistry.{method} exists but is not callable"

    def test_singleton_instance_exists(self):
        """Verify agent_registry singleton is available."""
        assert agent_registry is not None
        assert isinstance(agent_registry, AgentRegistry)

    def test_list_agents_returns_dict(self):
        """list_agents() must return dict of agents."""
        result = agent_registry.list_agents()
        assert isinstance(result, dict)
        # Can be empty, but should be a dict

    def test_summarize_agents_returns_list(self):
        """summarize_agents() must return list of agent summaries."""
        result = agent_registry.summarize_agents()
        assert isinstance(result, list)
        # Can be empty, but should be a list

    def test_get_agent_returns_optional(self):
        """get_agent() returns None or agent instance."""
        result = agent_registry.get_agent("nonexistent_agent")
        assert result is None

    def test_get_contract_returns_optional(self):
        """get_contract() returns None or contract."""
        result = agent_registry.get_contract("nonexistent_agent")
        assert result is None


class TestAgentIntegration:
    """Integration tests for agent contract stability."""

    def test_can_create_concrete_agent(self):
        """Should be able to create a concrete agent by implementing abstract methods."""
        class TestAgent(BaseAgent):
            def _register_message_handlers(self):
                self.register_handler("test", self.handle_test)

            def get_contract(self) -> AgentContract:
                return AgentContract(
                    agent_id=self.agent_id,
                    name="TestAgent",
                    version="1.0.0",
                    capabilities=[],
                    checkpoints=[],
                    max_runtime_s=100,
                    confidence_threshold=0.8,
                    side_effects=[]
                )

            async def handle_test(self, params):
                return {"result": "ok"}

        agent = TestAgent()
        assert agent is not None
        assert agent.status == AgentStatus.READY
        assert agent.agent_id is not None

    def test_agent_status_flow(self):
        """Agent status should follow expected lifecycle."""
        class TestAgent(BaseAgent):
            def _register_message_handlers(self):
                pass

            def get_contract(self) -> AgentContract:
                return AgentContract(
                    agent_id=self.agent_id,
                    name="TestAgent",
                    version="1.0.0",
                    capabilities=[],
                    checkpoints=[],
                    max_runtime_s=100,
                    confidence_threshold=0.8,
                    side_effects=[]
                )

        agent = TestAgent()

        # Should start READY after successful init
        assert agent.status == AgentStatus.READY

        # Statistics should be initialized
        assert isinstance(agent.statistics, dict)
        assert "requests_processed" in agent.statistics
        assert "error_count" in agent.statistics

    def test_message_handler_registration(self):
        """Should be able to register and retrieve handlers."""
        class TestAgent(BaseAgent):
            def _register_message_handlers(self):
                self.register_handler("test_method", self.handle_test)

            def get_contract(self) -> AgentContract:
                return AgentContract(
                    agent_id=self.agent_id,
                    name="TestAgent",
                    version="1.0.0",
                    capabilities=[],
                    checkpoints=[],
                    max_runtime_s=100,
                    confidence_threshold=0.8,
                    side_effects=[]
                )

            async def handle_test(self, params):
                return {"status": "success"}

        agent = TestAgent()

        # Handler should be registered
        assert "test_method" in agent.message_handlers
        assert callable(agent.message_handlers["test_method"])
