"""
Unit tests for the Model Manager module.
"""

import pytest
from pathlib import Path
import json
from shared.models.model_manager import ModelManager


@pytest.mark.unit
def test_models_config_exists():
    """Test that models configuration file exists."""
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'
    assert config_path.exists(), "models_config.json should exist"


@pytest.mark.unit
def test_models_config_valid_json():
    """Test that models configuration is valid JSON."""
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'

    with open(config_path, 'r') as f:
        config = json.load(f)

    assert isinstance(config, dict), "Config should be a dictionary"
    assert 'available_models' in config, "Config should have 'available_models' key"
    assert 'default_model' in config, "Config should have 'default_model' key"


@pytest.mark.unit
def test_models_config_has_required_models():
    """Test that essential models are configured."""
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'

    with open(config_path, 'r') as f:
        config = json.load(f)

    models = config['available_models']

    # Check for essential model types
    model_ids = [model['id'] for model in models.values()]

    # At least one OCR-based model should exist
    assert any('ocr' in model_id.lower() for model_id in model_ids), \
        "Should have at least one OCR-based model"


@pytest.mark.unit
def test_default_model_exists():
    """Test that the default model is in available models."""
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'

    with open(config_path, 'r') as f:
        config = json.load(f)

    default_model = config['default_model']
    available_model_ids = [model['id'] for model in config['available_models'].values()]

    assert default_model in available_model_ids, \
        f"Default model '{default_model}' should be in available models"


@pytest.mark.unit
def test_model_schema():
    """Test that each model has required fields."""
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'

    with open(config_path, 'r') as f:
        config = json.load(f)

    required_fields = ['id', 'name', 'type', 'description']

    for model_key, model in config['available_models'].items():
        for field in required_fields:
            assert field in model, \
                f"Model '{model_key}' should have '{field}' field"

        # Validate field types
        assert isinstance(model['id'], str), f"Model '{model_key}' id should be string"
        assert isinstance(model['name'], str), f"Model '{model_key}' name should be string"
        assert isinstance(model['type'], str), f"Model '{model_key}' type should be string"
        assert isinstance(model['description'], str), f"Model '{model_key}' description should be string"


@pytest.mark.unit
def test_model_manager_initialization():
    """Test ModelManager can be initialized."""
    manager = ModelManager()
    assert manager is not None
    assert manager.models_config is not None
    assert 'available_models' in manager.models_config


@pytest.mark.unit
def test_model_manager_get_available_models():
    """Test getting list of available models."""
    manager = ModelManager()
    models = manager.get_available_models()

    assert isinstance(models, list)
    assert len(models) > 0

    # Check that each model has required fields
    for model in models:
        assert 'id' in model
        assert 'name' in model
        assert 'type' in model
        assert 'description' in model


@pytest.mark.unit
def test_model_manager_get_default_model():
    """Test getting the default model."""
    manager = ModelManager()
    default_model = manager.get_default_model()

    assert isinstance(default_model, str)
    assert len(default_model) > 0


@pytest.mark.unit
def test_model_manager_select_model():
    """Test selecting a model."""
    manager = ModelManager()
    default_model = manager.get_default_model()

    # Test selecting a valid model
    result = manager.select_model(default_model)
    assert result is True
    assert manager.get_current_model() == default_model

    # Test selecting an invalid model
    result = manager.select_model('nonexistent_model')
    assert result is False


@pytest.mark.unit
def test_model_manager_get_model_info():
    """Test getting model information."""
    manager = ModelManager()
    default_model = manager.get_default_model()

    model_info = manager.get_model_info(default_model)
    assert model_info is not None
    assert 'id' in model_info
    assert 'name' in model_info
    assert 'type' in model_info


@pytest.mark.unit
def test_model_manager_filter_by_capability():
    """Test filtering models by capability."""
    manager = ModelManager()

    # Get all models and check their capabilities
    models = manager.get_available_models()

    # This test validates the filter method works, even if no models match
    filtered = manager.filter_models_by_capability('some_capability')
    assert isinstance(filtered, list)
