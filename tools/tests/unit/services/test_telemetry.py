"""
Tests for telemetry utilities module
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from shared.utils.telemetry import (
    get_tracer,
    trace_function,
    set_span_attributes,
    sanitize_attributes
)


class TestGetTracer:
    """Tests for get_tracer function"""
    
    def test_get_tracer_returns_tracer(self):
        """Test that get_tracer returns a tracer object"""
        tracer = get_tracer()
        assert tracer is not None
        assert hasattr(tracer, 'start_as_current_span')
    
    def test_get_tracer_with_name(self):
        """Test that get_tracer accepts a name parameter"""
        tracer = get_tracer("test_tracer")
        assert tracer is not None


class TestTraceFunction:
    """Tests for trace_function decorator"""
    
    def test_trace_function_basic(self):
        """Test basic trace_function decorator"""
        @trace_function("test_span")
        def test_func():
            return "result"
        
        result = test_func()
        assert result == "result"
    
    def test_trace_function_with_attributes(self):
        """Test trace_function with attributes"""
        @trace_function("test_span", attributes={"key": "value"})
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
    
    def test_trace_function_with_exception(self):
        """Test trace_function handles exceptions"""
        @trace_function("test_span")
        def test_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError, match="test error"):
            test_func()


class TestSetSpanAttributes:
    """Tests for set_span_attributes function"""
    
    def test_set_span_attributes_basic(self):
        """Test setting basic attributes"""
        span = Mock()
        attributes = {"key1": "value1", "key2": 42}
        
        set_span_attributes(span, attributes)
        
        assert span.set_attribute.call_count == 2
    
    def test_set_span_attributes_with_none(self):
        """Test setting attributes with None values"""
        span = Mock()
        attributes = {"key1": "value1", "key2": None}
        
        set_span_attributes(span, attributes)
        
        # Should only set key1
        assert span.set_attribute.call_count == 2
    
    def test_set_span_attributes_empty(self):
        """Test with empty attributes"""
        span = Mock()
        
        set_span_attributes(span, {})
        set_span_attributes(span, None)
        
        assert span.set_attribute.call_count == 0


class TestSanitizeAttributes:
    """Tests for sanitize_attributes function"""
    
    def test_sanitize_basic(self):
        """Test basic sanitization"""
        attributes = {
            "name": "John",
            "password": "secret123",
            "token": "abc123"
        }
        
        sanitized = sanitize_attributes(attributes)
        
        assert sanitized["name"] == "John"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"
    
    def test_sanitize_custom_keys(self):
        """Test sanitization with custom sensitive keys"""
        attributes = {
            "username": "john",
            "api_key": "secret",
            "data": "value"
        }
        
        sanitized = sanitize_attributes(attributes, sensitive_keys=["api_key"])
        
        assert sanitized["username"] == "john"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["data"] == "value"
    
    def test_sanitize_case_insensitive(self):
        """Test that sanitization is case-insensitive"""
        attributes = {
            "Password": "secret",
            "API_KEY": "secret",
            "Token": "secret"
        }
        
        sanitized = sanitize_attributes(attributes)
        
        assert sanitized["Password"] == "***REDACTED***"
        assert sanitized["API_KEY"] == "***REDACTED***"
        assert sanitized["Token"] == "***REDACTED***"
