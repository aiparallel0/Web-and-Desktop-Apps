"""
=============================================================================
CIRCULAR EXCHANGE COMPLIANT TEST MODULE
=============================================================================

Module: tests.circular_exchange.test_project_config
Path: tests/circular_exchange/test_project_config.py
Description: Tests for ProjectConfiguration - Variable-Based Configuration Hub
Compliance Version: 2.0.0

=============================================================================
"""

import pytest
import sys
from pathlib import Path

# Add shared to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from circular_exchange.project_config import (
    PROJECT_CONFIG,
    ProjectConfiguration,
    ModuleRegistration,
    SecurityPolicy,
    CodingStandards
)
from circular_exchange.variable_package import PackageChange


class TestProjectConfiguration:
    """Tests for ProjectConfiguration singleton."""

    def test_singleton_pattern(self):
        """Test that ProjectConfiguration is a singleton."""
        config1 = ProjectConfiguration()
        config2 = ProjectConfiguration()
        assert config1 is config2

    def test_global_instance(self):
        """Test that PROJECT_CONFIG is properly initialized."""
        assert PROJECT_CONFIG is not None
        assert isinstance(PROJECT_CONFIG, ProjectConfiguration)

    def test_debug_package(self):
        """Test debug configuration package."""
        assert PROJECT_CONFIG.debug is not None
        assert isinstance(PROJECT_CONFIG.debug.value, bool)
        assert PROJECT_CONFIG.debug.value is False  # Default

    def test_project_name(self):
        """Test project name configuration."""
        assert PROJECT_CONFIG.project_name.value == "Receipt Extractor"

    def test_project_version(self):
        """Test project version configuration."""
        assert PROJECT_CONFIG.project_version.value == "3.0.0"


class TestSecurityPolicy:
    """Tests for SecurityPolicy configuration."""

    def test_security_policy_defaults(self):
        """Test security policy default values."""
        policy = PROJECT_CONFIG.security_policy.value
        assert isinstance(policy, SecurityPolicy)
        assert policy.require_authentication is True
        assert policy.enable_rate_limiting is True
        assert policy.max_requests_per_minute == 100
        assert policy.enable_input_validation is True
        assert policy.enable_output_sanitization is True
        assert policy.log_security_events is True


class TestCodingStandards:
    """Tests for CodingStandards configuration."""

    def test_coding_standards_defaults(self):
        """Test coding standards default values."""
        standards = PROJECT_CONFIG.coding_standards.value
        assert isinstance(standards, CodingStandards)
        assert standards.use_type_hints is True
        assert standards.require_docstrings is True
        assert standards.max_function_length == 50
        assert standards.max_file_length == 500
        assert standards.require_error_handling is True
        assert standards.use_logging is True
        assert standards.follow_pep8 is True


class TestModuleRegistration:
    """Tests for module registration functionality."""

    def test_register_module(self):
        """Test registering a module."""
        registration = ModuleRegistration(
            module_id="test.module",
            file_path="test/module.py",
            description="Test module for testing",
            dependencies=["shared.circular_exchange"],
            exports=["TestClass", "test_function"],
            is_circular_exchange_compliant=True,
            compliance_version="2.0.0"
        )
        
        PROJECT_CONFIG.register_module(registration)
        
        retrieved = PROJECT_CONFIG.get_module("test.module")
        assert retrieved is not None
        assert retrieved.module_id == "test.module"
        assert retrieved.description == "Test module for testing"
        assert "shared.circular_exchange" in retrieved.dependencies

    def test_get_all_modules(self):
        """Test getting all registered modules."""
        modules = PROJECT_CONFIG.get_all_modules()
        assert isinstance(modules, dict)
        # project_config should be registered
        assert "project_config" in modules

    def test_get_nonexistent_module(self):
        """Test getting a module that doesn't exist."""
        result = PROJECT_CONFIG.get_module("nonexistent.module")
        assert result is None


class TestConfigurationUpdate:
    """Tests for configuration update functionality."""

    def test_update_debug_config(self):
        """Test updating debug configuration."""
        original_value = PROJECT_CONFIG.debug.value
        
        result = PROJECT_CONFIG.update_config("debug", True)
        assert result is True
        assert PROJECT_CONFIG.debug.value is True
        
        # Restore original value
        PROJECT_CONFIG.update_config("debug", original_value)

    def test_update_nonexistent_config(self):
        """Test updating a config that doesn't exist."""
        result = PROJECT_CONFIG.update_config("nonexistent", "value")
        assert result is False


class TestConfigurationPaths:
    """Tests for paths configuration."""

    def test_paths_config(self):
        """Test paths configuration."""
        paths = PROJECT_CONFIG.paths.value
        assert "root" in paths
        assert "shared" in paths
        assert paths["shared"] == "shared"
        assert paths["models"] == "shared/models"
        assert paths["utils"] == "shared/utils"


class TestAIAgentConfiguration:
    """Tests for AI agent configuration."""

    def test_ai_agent_config(self):
        """Test AI agent configuration."""
        ai_config = PROJECT_CONFIG.ai_agent_config.value
        assert ai_config["must_use_circular_exchange"] is True
        assert ai_config["must_register_modules"] is True
        assert ai_config["must_use_variable_packages"] is True
        assert ai_config["must_add_compliance_headers"] is True
        assert "compliance_header_template" in ai_config
        assert "import_structure" in ai_config


class TestComplianceHeader:
    """Tests for compliance header generation."""

    def test_get_compliance_header(self):
        """Test generating compliance header."""
        header = PROJECT_CONFIG.get_compliance_header(
            module_name="test.module",
            file_path="test/module.py",
            description="Test module",
            dependencies=["shared.utils"],
            exports=["TestClass"]
        )
        
        assert "CIRCULAR EXCHANGE COMPLIANT MODULE" in header
        assert "test.module" in header
        assert "test/module.py" in header
        assert "Test module" in header
        assert "shared.utils" in header
        assert "TestClass" in header


class TestSubscription:
    """Tests for configuration subscription."""

    def test_subscribe_to_all(self):
        """Test subscribing to all configuration changes."""
        changes = []
        
        def callback(package_name, change):
            changes.append((package_name, change))
        
        unsubscribers = PROJECT_CONFIG.subscribe_to_all(callback)
        
        # Make a change
        original = PROJECT_CONFIG.debug.value
        PROJECT_CONFIG.debug.set(not original)
        
        # Should have received the change
        assert len(changes) >= 1
        assert any(c[0] == "debug" for c in changes)
        
        # Cleanup
        for unsub in unsubscribers:
            unsub()
        PROJECT_CONFIG.debug.set(original)
