"""
Unit tests for the Model Manager module.
"""

import pytest
from pathlib import Path
import json


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


# Placeholder for future model manager tests
# These will require the actual model manager implementation to be imported

@pytest.mark.unit
@pytest.mark.skip(reason="Model manager module needs to be implemented")
def test_model_manager_load_model():
    """Test loading a model through model manager."""
    pass


@pytest.mark.unit
@pytest.mark.skip(reason="Model manager module needs to be implemented")
def test_model_manager_switch_models():
    """Test switching between different models."""
    pass
