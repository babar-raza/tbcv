"""
Comprehensive tests for core.access_guard module.

Tests cover:
- Enforcement mode configuration
- Stack inspection and caller detection
- Access guard decorator functionality
- Violation logging and statistics
- Block and warn behaviors
- Edge cases and error handling
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from core.access_guard import (
    EnforcementMode,
    AccessGuardError,
    set_enforcement_mode,
    get_enforcement_mode,
    check_caller_allowed,
    log_violation,
    guarded_operation,
    is_guarded,
    reset_statistics,
    get_statistics,
    _initialize_from_env
)


class TestEnforcementMode:
    """Tests for EnforcementMode enum."""

    def test_enum_values(self):
        """Test that enum has correct values."""
        assert EnforcementMode.DISABLED.value == "disabled"
        assert EnforcementMode.WARN.value == "warn"
        assert EnforcementMode.BLOCK.value == "block"

    def test_from_string_lowercase(self):
        """Test creating mode from lowercase string."""
        assert EnforcementMode.from_string("disabled") == EnforcementMode.DISABLED
        assert EnforcementMode.from_string("warn") == EnforcementMode.WARN
        assert EnforcementMode.from_string("block") == EnforcementMode.BLOCK

    def test_from_string_uppercase(self):
        """Test creating mode from uppercase string."""
        assert EnforcementMode.from_string("DISABLED") == EnforcementMode.DISABLED
        assert EnforcementMode.from_string("WARN") == EnforcementMode.WARN
        assert EnforcementMode.from_string("BLOCK") == EnforcementMode.BLOCK

    def test_from_string_mixed_case(self):
        """Test creating mode from mixed case string."""
        assert EnforcementMode.from_string("Disabled") == EnforcementMode.DISABLED
        assert EnforcementMode.from_string("WaRn") == EnforcementMode.WARN
        assert EnforcementMode.from_string("BlOcK") == EnforcementMode.BLOCK

    def test_from_string_invalid(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid enforcement mode"):
            EnforcementMode.from_string("invalid")


class TestAccessGuardError:
    """Tests for AccessGuardError exception."""

    def test_error_creation_default_message(self):
        """Test error creation with default message."""
        error = AccessGuardError("my_function", "api/server.py:123")

        assert error.function_name == "my_function"
        assert error.caller_info == "api/server.py:123"
        assert "my_function" in error.message
        assert "api/server.py:123" in error.message
        assert "MCP client" in error.message

    def test_error_creation_custom_message(self):
        """Test error creation with custom message."""
        custom_msg = "Custom violation message"
        error = AccessGuardError("my_function", "caller_info", custom_msg)

        assert error.message == custom_msg
        assert str(error) == custom_msg

    def test_error_is_exception(self):
        """Test that AccessGuardError is a proper exception."""
        error = AccessGuardError("func", "caller")
        assert isinstance(error, Exception)


class TestEnforcementModeConfiguration:
    """Tests for setting and getting enforcement mode."""

    def setup_method(self):
        """Reset enforcement mode before each test."""
        set_enforcement_mode(EnforcementMode.DISABLED)
        reset_statistics()

    def test_set_mode_with_enum(self):
        """Test setting mode with EnforcementMode enum."""
        set_enforcement_mode(EnforcementMode.WARN)
        assert get_enforcement_mode() == EnforcementMode.WARN

        set_enforcement_mode(EnforcementMode.BLOCK)
        assert get_enforcement_mode() == EnforcementMode.BLOCK

    def test_set_mode_with_string(self):
        """Test setting mode with string."""
        set_enforcement_mode("warn")
        assert get_enforcement_mode() == EnforcementMode.WARN

        set_enforcement_mode("block")
        assert get_enforcement_mode() == EnforcementMode.BLOCK

        set_enforcement_mode("disabled")
        assert get_enforcement_mode() == EnforcementMode.DISABLED

    def test_set_mode_invalid_string(self):
        """Test setting mode with invalid string raises error."""
        with pytest.raises(ValueError):
            set_enforcement_mode("invalid_mode")

    def test_mode_persists(self):
        """Test that mode setting persists."""
        set_enforcement_mode(EnforcementMode.BLOCK)
        assert get_enforcement_mode() == EnforcementMode.BLOCK

        # Should still be BLOCK after another call
        mode = get_enforcement_mode()
        assert mode == EnforcementMode.BLOCK


class TestCallerDetection:
    """Tests for check_caller_allowed stack inspection."""

    def test_check_from_test_context(self):
        """Test that calls from test context are allowed."""
        allowed, info = check_caller_allowed()

        # This test is in tests/ directory, so should be allowed
        assert allowed is True
        assert "Test code" in info or "Internal call" in info

    def test_check_internal_call(self):
        """Test that internal calls are allowed by default."""
        def internal_function():
            return check_caller_allowed()

        allowed, info = internal_function()

        # Should be allowed (either as test code or internal call)
        assert allowed is True

    @patch('inspect.stack')
    def test_check_mcp_server_allowed(self, mock_stack):
        """Test that calls from MCP server are allowed."""
        mock_frame = MagicMock()
        mock_frame.filename = "/path/to/svc/mcp_server.py"
        mock_frame.function = "handle_request"
        mock_frame.lineno = 123

        mock_stack.return_value = [
            MagicMock(),  # Current frame
            mock_frame    # Caller frame
        ]

        allowed, info = check_caller_allowed()

        assert allowed is True
        assert "MCP server" in info
        assert "mcp_server.py" in info

    @patch('inspect.stack')
    def test_check_mcp_methods_allowed(self, mock_stack):
        """Test that calls from MCP methods are allowed."""
        mock_frame = MagicMock()
        mock_frame.filename = "/path/to/svc/mcp_methods/validation_methods.py"
        mock_frame.function = "validate_content"
        mock_frame.lineno = 45

        mock_stack.return_value = [
            MagicMock(),
            mock_frame
        ]

        allowed, info = check_caller_allowed()

        assert allowed is True
        assert "MCP method" in info
        assert "validation_methods.py" in info

    @patch('inspect.stack')
    def test_check_api_blocked(self, mock_stack):
        """Test that calls from API endpoints are blocked."""
        mock_frame = MagicMock()
        mock_frame.filename = "/path/to/api/server.py"
        mock_frame.function = "validate_endpoint"
        mock_frame.lineno = 78

        mock_stack.return_value = [
            MagicMock(),
            mock_frame
        ]

        allowed, info = check_caller_allowed()

        assert allowed is False
        assert "API endpoint" in info
        assert "server.py" in info

    @patch('inspect.stack')
    def test_check_cli_blocked(self, mock_stack):
        """Test that calls from CLI commands are blocked."""
        mock_frame = MagicMock()
        mock_frame.filename = "/path/to/cli/main.py"
        mock_frame.function = "validate_command"
        mock_frame.lineno = 90

        mock_stack.return_value = [
            MagicMock(),
            mock_frame
        ]

        allowed, info = check_caller_allowed()

        assert allowed is False
        assert "CLI command" in info
        assert "main.py" in info

    @patch('inspect.stack')
    def test_check_mcp_client_allowed(self, mock_stack):
        """Test that calls from MCP client are allowed."""
        mock_frame = MagicMock()
        mock_frame.filename = "/path/to/svc/mcp_client.py"
        mock_frame.function = "call_tool"
        mock_frame.lineno = 100

        mock_stack.return_value = [
            MagicMock(),
            mock_frame
        ]

        allowed, info = check_caller_allowed()

        assert allowed is True
        assert "MCP client" in info

    @patch('inspect.stack')
    def test_check_windows_paths(self, mock_stack):
        """Test that Windows paths are handled correctly."""
        mock_frame = MagicMock()
        mock_frame.filename = "C:\\path\\to\\api\\server.py"
        mock_frame.function = "endpoint"
        mock_frame.lineno = 50

        mock_stack.return_value = [
            MagicMock(),
            mock_frame
        ]

        allowed, info = check_caller_allowed()

        assert allowed is False
        assert "API endpoint" in info


class TestViolationLogging:
    """Tests for violation logging and statistics."""

    def setup_method(self):
        """Reset statistics before each test."""
        reset_statistics()

    def test_reset_statistics(self):
        """Test that reset_statistics clears all stats."""
        log_violation("test_func", "caller", EnforcementMode.WARN)
        reset_statistics()

        stats = get_statistics()
        assert stats["violation_count"] == 0
        assert len(stats["recent_violations"]) == 0

    def test_log_violation_increments_count(self):
        """Test that logging violations increments count."""
        log_violation("func1", "caller1", EnforcementMode.WARN)
        log_violation("func2", "caller2", EnforcementMode.WARN)

        stats = get_statistics()
        assert stats["violation_count"] == 2

    def test_log_violation_records_details(self):
        """Test that violation details are recorded."""
        log_violation(
            "test_function",
            "api/server.py:123",
            EnforcementMode.WARN,
            {"extra": "context"}
        )

        stats = get_statistics()
        violations = stats["recent_violations"]

        assert len(violations) == 1
        violation = violations[0]

        assert violation["function_name"] == "test_function"
        assert violation["caller_info"] == "api/server.py:123"
        assert violation["mode"] == "warn"
        assert violation["extra"] == "context"
        assert "timestamp" in violation

    def test_get_statistics_includes_mode(self):
        """Test that statistics include current mode."""
        set_enforcement_mode(EnforcementMode.BLOCK)
        stats = get_statistics()

        assert stats["mode"] == "block"

    def test_statistics_limits_recent_violations(self):
        """Test that only last 100 violations are kept."""
        # Log more than 100 violations
        for i in range(150):
            log_violation(f"func_{i}", f"caller_{i}", EnforcementMode.WARN)

        stats = get_statistics()
        assert stats["violation_count"] == 150
        assert len(stats["recent_violations"]) == 100


class TestGuardedOperationDecorator:
    """Tests for @guarded_operation decorator."""

    def setup_method(self):
        """Reset state before each test."""
        set_enforcement_mode(EnforcementMode.DISABLED)
        reset_statistics()

    def test_disabled_mode_allows_all(self):
        """Test that DISABLED mode allows all calls."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        @guarded_operation
        def protected_func():
            return "success"

        result = protected_func()
        assert result == "success"

        stats = get_statistics()
        assert stats["violation_count"] == 0

    def test_warn_mode_logs_but_allows(self):
        """Test that WARN mode logs violations but allows execution."""
        set_enforcement_mode(EnforcementMode.WARN)

        @guarded_operation
        def protected_func():
            return "executed"

        # Should execute without error
        result = protected_func()
        assert result == "executed"

        # But should log violation (we're calling from test, which is allowed)
        # So actually no violation in this case
        # Let's test with mocked stack instead

    @patch('core.access_guard.check_caller_allowed')
    def test_warn_mode_with_violation(self, mock_check):
        """Test WARN mode with actual violation."""
        set_enforcement_mode(EnforcementMode.WARN)
        mock_check.return_value = (False, "api/server.py:123")

        @guarded_operation
        def protected_func():
            return "executed"

        result = protected_func()
        assert result == "executed"

        stats = get_statistics()
        assert stats["violation_count"] == 1

    @patch('core.access_guard.check_caller_allowed')
    def test_block_mode_raises_error(self, mock_check):
        """Test that BLOCK mode raises AccessGuardError."""
        set_enforcement_mode(EnforcementMode.BLOCK)
        mock_check.return_value = (False, "api/server.py:123")

        @guarded_operation
        def protected_func():
            return "should not execute"

        with pytest.raises(AccessGuardError) as exc_info:
            protected_func()

        error = exc_info.value
        assert "protected_func" in error.function_name
        assert "api/server.py:123" in error.caller_info

    @patch('core.access_guard.check_caller_allowed')
    def test_block_mode_logs_violation(self, mock_check):
        """Test that BLOCK mode logs violation before raising."""
        set_enforcement_mode(EnforcementMode.BLOCK)
        mock_check.return_value = (False, "api/server.py:123")

        @guarded_operation
        def protected_func():
            return "should not execute"

        with pytest.raises(AccessGuardError):
            protected_func()

        stats = get_statistics()
        assert stats["violation_count"] == 1

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @guarded_operation
        def my_function(arg1, arg2):
            """Test docstring."""
            return arg1 + arg2

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "Test docstring."
        assert hasattr(my_function, "__wrapped__")
        assert hasattr(my_function, "__guarded__")

    def test_decorator_works_with_arguments(self):
        """Test that decorated function works with arguments."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        @guarded_operation
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_decorator_works_with_kwargs(self):
        """Test that decorated function works with keyword arguments."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        @guarded_operation
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = greet("Alice", greeting="Hi")
        assert result == "Hi, Alice!"

    def test_decorator_on_method(self):
        """Test that decorator works on class methods."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        class MyClass:
            @guarded_operation
            def my_method(self, value):
                return value * 2

        obj = MyClass()
        result = obj.my_method(5)
        assert result == 10

    @patch('core.access_guard.check_caller_allowed')
    def test_violation_includes_args_info(self, mock_check):
        """Test that violation log includes argument information."""
        set_enforcement_mode(EnforcementMode.WARN)
        mock_check.return_value = (False, "api/server.py")

        @guarded_operation
        def func_with_args(a, b, c=None):
            return "result"

        func_with_args(1, 2, c=3)

        stats = get_statistics()
        violation = stats["recent_violations"][0]

        # args_count is 2 (positional args only), c is in kwargs
        assert violation["args_count"] == 2
        assert "c" in violation["kwargs_keys"]


class TestIsGuarded:
    """Tests for is_guarded helper function."""

    def test_is_guarded_true(self):
        """Test that is_guarded returns True for guarded functions."""
        @guarded_operation
        def protected_func():
            pass

        assert is_guarded(protected_func) is True

    def test_is_guarded_false(self):
        """Test that is_guarded returns False for unguarded functions."""
        def unprotected_func():
            pass

        assert is_guarded(unprotected_func) is False

    def test_is_guarded_on_method(self):
        """Test is_guarded on class methods."""
        class MyClass:
            @guarded_operation
            def protected(self):
                pass

            def unprotected(self):
                pass

        obj = MyClass()
        assert is_guarded(obj.protected) is True
        assert is_guarded(obj.unprotected) is False


class TestEnvironmentInitialization:
    """Tests for environment variable initialization."""

    def test_env_initialization_warn(self, monkeypatch):
        """Test initialization from TBCV_ACCESS_GUARD_MODE=warn."""
        monkeypatch.setenv("TBCV_ACCESS_GUARD_MODE", "warn")

        # Re-initialize
        _initialize_from_env()

        assert get_enforcement_mode() == EnforcementMode.WARN

    def test_env_initialization_block(self, monkeypatch):
        """Test initialization from TBCV_ACCESS_GUARD_MODE=block."""
        monkeypatch.setenv("TBCV_ACCESS_GUARD_MODE", "block")

        _initialize_from_env()

        assert get_enforcement_mode() == EnforcementMode.BLOCK

    def test_env_initialization_invalid(self, monkeypatch):
        """Test that invalid env value doesn't crash."""
        monkeypatch.setenv("TBCV_ACCESS_GUARD_MODE", "invalid")

        # Should log warning but not crash
        _initialize_from_env()

        # Mode should remain unchanged
        mode = get_enforcement_mode()
        assert mode in [EnforcementMode.DISABLED, EnforcementMode.WARN, EnforcementMode.BLOCK]

    def test_no_env_variable(self, monkeypatch):
        """Test behavior when env variable is not set."""
        monkeypatch.delenv("TBCV_ACCESS_GUARD_MODE", raising=False)

        # Should not crash
        _initialize_from_env()


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios."""

    def setup_method(self):
        """Reset state before each test."""
        set_enforcement_mode(EnforcementMode.DISABLED)
        reset_statistics()

    @patch('core.access_guard.check_caller_allowed')
    def test_api_to_business_logic_blocked(self, mock_check):
        """Test that API cannot directly call business logic."""
        set_enforcement_mode(EnforcementMode.BLOCK)
        mock_check.return_value = (False, "api/server.py:validate_endpoint")

        @guarded_operation
        def validate_content(file_path: str):
            return {"valid": True}

        with pytest.raises(AccessGuardError) as exc_info:
            validate_content("test.md")

        assert "validate_content" in str(exc_info.value)
        assert "MCP client" in str(exc_info.value)

    @patch('core.access_guard.check_caller_allowed')
    def test_mcp_to_business_logic_allowed(self, mock_check):
        """Test that MCP layer can call business logic."""
        set_enforcement_mode(EnforcementMode.BLOCK)
        mock_check.return_value = (True, "svc/mcp_methods/validation_methods.py")

        @guarded_operation
        def validate_content(file_path: str):
            return {"valid": True}

        result = validate_content("test.md")
        assert result == {"valid": True}

    def test_multiple_violations_tracked(self):
        """Test that multiple violations are tracked correctly."""
        set_enforcement_mode(EnforcementMode.WARN)

        with patch('core.access_guard.check_caller_allowed') as mock_check:
            mock_check.return_value = (False, "api/server.py")

            @guarded_operation
            def func1():
                return 1

            @guarded_operation
            def func2():
                return 2

            func1()
            func2()
            func1()

        stats = get_statistics()
        assert stats["violation_count"] == 3
        assert len(stats["recent_violations"]) == 3

    def test_mixed_enforcement_modes(self):
        """Test changing enforcement modes during runtime."""
        @guarded_operation
        def protected_func():
            return "result"

        with patch('core.access_guard.check_caller_allowed') as mock_check:
            mock_check.return_value = (False, "api/server.py")

            # Start in DISABLED
            set_enforcement_mode(EnforcementMode.DISABLED)
            result = protected_func()
            assert result == "result"

            # Switch to WARN
            set_enforcement_mode(EnforcementMode.WARN)
            result = protected_func()
            assert result == "result"
            assert get_statistics()["violation_count"] == 1

            # Switch to BLOCK
            set_enforcement_mode(EnforcementMode.BLOCK)
            with pytest.raises(AccessGuardError):
                protected_func()


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def setup_method(self):
        """Reset state before each test."""
        set_enforcement_mode(EnforcementMode.DISABLED)
        reset_statistics()

    def test_deeply_nested_calls(self):
        """Test that deeply nested calls are handled correctly."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        @guarded_operation
        def level_3():
            return "level 3"

        @guarded_operation
        def level_2():
            return level_3()

        @guarded_operation
        def level_1():
            return level_2()

        result = level_1()
        assert result == "level 3"

    def test_recursive_function(self):
        """Test that recursive functions work correctly."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        @guarded_operation
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)

        result = factorial(5)
        assert result == 120

    def test_exception_in_guarded_function(self):
        """Test that exceptions in guarded functions propagate correctly."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        @guarded_operation
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_func()

    @patch('core.access_guard.check_caller_allowed')
    def test_exception_in_blocked_function_not_executed(self, mock_check):
        """Test that blocked functions don't execute (and don't raise their exceptions)."""
        set_enforcement_mode(EnforcementMode.BLOCK)
        mock_check.return_value = (False, "api/server.py")

        @guarded_operation
        def failing_func():
            raise ValueError("Should not execute")

        # Should raise AccessGuardError, not ValueError
        with pytest.raises(AccessGuardError):
            failing_func()

    def test_none_return_value(self):
        """Test that functions returning None work correctly."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        @guarded_operation
        def returns_none():
            return None

        result = returns_none()
        assert result is None

    def test_generator_function(self):
        """Test that generator functions work with decorator."""
        set_enforcement_mode(EnforcementMode.DISABLED)

        @guarded_operation
        def generate_numbers():
            for i in range(3):
                yield i

        result = list(generate_numbers())
        assert result == [0, 1, 2]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
