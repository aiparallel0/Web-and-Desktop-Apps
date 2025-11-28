import pytest
from pathlib import Path
import json
from shared.models.model_manager import ModelManager

@pytest.mark.unit
def test_models_config_exists():
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'
    assert config_path.exists(), "models_config.json should exist"

@pytest.mark.unit
def test_models_config_valid_json():
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    assert isinstance(config, dict), "Config should be a dictionary"
    assert 'available_models' in config, "Config should have 'available_models' key"
    assert 'default_model' in config, "Config should have 'default_model' key"

@pytest.mark.unit
def test_models_config_has_required_models():
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    models = config['available_models']
    model_ids = [model['id'] for model in models.values()]
    assert any('ocr' in model_id.lower() for model_id in model_ids), \
        "Should have at least one OCR-based model"

@pytest.mark.unit
def test_default_model_exists():
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    default_model = config['default_model']
    available_model_ids = [model['id'] for model in config['available_models'].values()]
    assert default_model in available_model_ids, \
        f"Default model '{default_model}' should be in available models"

@pytest.mark.unit
def test_model_schema():
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    required_fields = ['id', 'name', 'type', 'description']
    for model_key, model in config['available_models'].items():
        for field in required_fields:
            assert field in model, \
                f"Model '{model_key}' should have '{field}' field"
        assert isinstance(model['id'], str), f"Model '{model_key}' id should be string"
        assert isinstance(model['name'], str), f"Model '{model_key}' name should be string"
        assert isinstance(model['type'], str), f"Model '{model_key}' type should be string"
        assert isinstance(model['description'], str), f"Model '{model_key}' description should be string"

@pytest.mark.unit
def test_model_manager_initialization():
    manager = ModelManager()
    assert manager is not None
    assert manager.models_config is not None
    assert 'available_models' in manager.models_config

@pytest.mark.unit
def test_model_manager_get_available_models():
    manager = ModelManager()
    models = manager.get_available_models()
    assert isinstance(models, list)
    assert len(models) > 0
    for model in models:
        assert 'id' in model
        assert 'name' in model
        assert 'type' in model
        assert 'description' in model

@pytest.mark.unit
def test_model_manager_get_default_model():
    manager = ModelManager()
    default_model = manager.get_default_model()
    assert isinstance(default_model, str)
    assert len(default_model) > 0

@pytest.mark.unit
def test_model_manager_select_model():
    manager = ModelManager()
    default_model = manager.get_default_model()
    result = manager.select_model(default_model)
    assert result is True
    assert manager.get_current_model() == default_model
    result = manager.select_model('nonexistent_model')
    assert result is False

@pytest.mark.unit
def test_model_manager_get_model_info():
    manager = ModelManager()
    default_model = manager.get_default_model()
    model_info = manager.get_model_info(default_model)
    assert model_info is not None
    assert 'id' in model_info
    assert 'name' in model_info
    assert 'type' in model_info

@pytest.mark.unit
def test_model_manager_filter_by_capability():
    manager = ModelManager()
    models = manager.get_available_models()
    filtered = manager.filter_models_by_capability('some_capability')
    assert isinstance(filtered, list)


@pytest.mark.unit
def test_model_manager_config_validation():
    """Test configuration validation"""
    manager = ModelManager()
    config = manager.models_config

    # Test valid config
    manager._validate_config(config)  # Should not raise

    # Test missing required field
    with pytest.raises(ValueError) as exc_info:
        manager._validate_config({})
    assert "available_models" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        manager._validate_config({'available_models': {}})
    assert "default_model" in str(exc_info.value)

    # Test invalid type for available_models
    with pytest.raises(ValueError) as exc_info:
        manager._validate_config({'available_models': [], 'default_model': 'test'})
    assert "must be an object" in str(exc_info.value) or "must be a dict" in str(exc_info.value).lower()


@pytest.mark.unit
def test_model_manager_config_validation_model_schema():
    """Test individual model configuration validation"""
    manager = ModelManager()

    # Test invalid model config - missing required fields
    with pytest.raises(ValueError) as exc_info:
        manager._validate_model_config('test_model', {})
    assert "missing required field" in str(exc_info.value)

    # Test invalid model type
    with pytest.raises(ValueError) as exc_info:
        manager._validate_model_config('test_model', {
            'id': 'test',
            'name': 'Test',
            'type': 'invalid_type',
            'description': 'Test model'
        })
    assert "invalid type" in str(exc_info.value)

    # Test donut model missing huggingface_id
    with pytest.raises(ValueError) as exc_info:
        manager._validate_model_config('test_donut', {
            'id': 'test',
            'name': 'Test',
            'type': 'donut',
            'description': 'Test model'
        })
    assert "huggingface_id" in str(exc_info.value)

    # Test donut model missing task_prompt
    with pytest.raises(ValueError) as exc_info:
        manager._validate_model_config('test_donut', {
            'id': 'test',
            'name': 'Test',
            'type': 'donut',
            'description': 'Test model',
            'huggingface_id': 'test/model'
        })
    assert "task_prompt" in str(exc_info.value)


@pytest.mark.unit
def test_model_manager_default_model_validation():
    """Test that default model exists in available models"""
    config_path = Path(__file__).parent.parent.parent / 'shared' / 'config' / 'models_config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)

    default_model = config['default_model']
    available_models = config['available_models']

    assert default_model in available_models, f"Default model '{default_model}' must exist in available models"


@pytest.mark.unit
def test_model_manager_get_processor_default():
    """Test getting processor with default model"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    # Select a model first
    manager.select_model(default_model)

    # Try to get processor (will fail if dependencies not installed, which is ok for testing structure)
    try:
        processor = manager.get_processor()
        # If we get here, processor was loaded successfully
        assert processor is not None
    except (ImportError, ValueError) as e:
        # Expected if dependencies not installed
        assert "requires" in str(e).lower() or "not found" in str(e).lower()


@pytest.mark.unit
def test_model_manager_get_processor_specific_model():
    """Test getting processor for specific model"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    try:
        processor = manager.get_processor(default_model)
        assert processor is not None
    except (ImportError, ValueError) as e:
        # Expected if dependencies not installed
        assert "requires" in str(e).lower() or "not found" in str(e).lower()


@pytest.mark.unit
def test_model_manager_unload_model():
    """Test unloading a specific model"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    # Try to load and unload
    try:
        processor = manager.get_processor(default_model)
        assert default_model in manager.loaded_processors

        manager.unload_model(default_model)
        assert default_model not in manager.loaded_processors
    except (ImportError, ValueError):
        # Can't test if dependencies not installed
        pass


@pytest.mark.unit
def test_model_manager_unload_all_models():
    """Test unloading all models"""
    manager = ModelManager()

    # Load a model
    try:
        default_model = manager.get_default_model()
        processor = manager.get_processor(default_model)

        assert len(manager.loaded_processors) > 0

        manager.unload_all_models()
        assert len(manager.loaded_processors) == 0
        assert len(manager.model_last_used) == 0
        assert len(manager.model_load_times) == 0
    except (ImportError, ValueError):
        # Can't test if dependencies not installed
        pass


@pytest.mark.unit
def test_model_manager_get_resource_stats():
    """Test getting resource statistics"""
    manager = ModelManager()
    stats = manager.get_resource_stats()

    assert 'loaded_models_count' in stats
    assert 'max_loaded_models' in stats
    assert 'current_model' in stats
    assert 'loaded_models' in stats
    assert 'model_usage' in stats

    assert isinstance(stats['loaded_models_count'], int)
    assert isinstance(stats['max_loaded_models'], int)
    assert isinstance(stats['loaded_models'], list)
    assert isinstance(stats['model_usage'], dict)


@pytest.mark.unit
def test_model_manager_get_model_capabilities():
    """Test getting model capabilities"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    capabilities = manager.get_model_capabilities(default_model)
    assert isinstance(capabilities, dict)

    # Test non-existent model
    capabilities = manager.get_model_capabilities('nonexistent_model')
    assert capabilities == {}


@pytest.mark.unit
def test_model_manager_load_config_error_handling():
    """Test config loading error handling"""
    import tempfile
    import os

    # Test with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('invalid json {')
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            manager = ModelManager(config_path=temp_path)
        assert "not valid JSON" in str(exc_info.value)
    finally:
        os.unlink(temp_path)

    # Test with missing file
    with pytest.raises(Exception):  # FileNotFoundError or similar
        manager = ModelManager(config_path='/nonexistent/path/config.json')


@pytest.mark.unit
def test_model_manager_processor_caching():
    """Test that processors are cached and reused"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    try:
        # Load processor twice
        processor1 = manager.get_processor(default_model)
        processor2 = manager.get_processor(default_model)

        # Should be the same cached instance
        assert processor1 is processor2
        assert default_model in manager.loaded_processors
    except (ImportError, ValueError):
        # Can't test if dependencies not installed
        pass


@pytest.mark.unit
def test_model_manager_max_loaded_models_eviction():
    """Test that LRU eviction works when max models exceeded"""
    manager = ModelManager(max_loaded_models=2)

    # This test requires models to actually load, which may not work without dependencies
    # So we'll test the eviction logic directly
    from datetime import datetime

    # Simulate having 2 models loaded
    manager.loaded_processors = {
        'model1': 'processor1',
        'model2': 'processor2'
    }
    manager.model_last_used = {
        'model1': datetime(2024, 1, 1),
        'model2': datetime(2024, 1, 2)
    }
    manager.model_load_times = {
        'model1': datetime(2024, 1, 1),
        'model2': datetime(2024, 1, 2)
    }

    # Call eviction directly
    manager._evict_least_recently_used()

    # model1 should be evicted (oldest)
    assert 'model1' not in manager.loaded_processors
    assert 'model2' in manager.loaded_processors


@pytest.mark.unit
def test_model_manager_get_processor_invalid_model():
    """Test getting processor for invalid model ID"""
    manager = ModelManager()

    with pytest.raises(ValueError) as exc_info:
        manager.get_processor('nonexistent_model_id_12345')

    assert "not found" in str(exc_info.value)


@pytest.mark.unit
def test_model_manager_threading_lock():
    """Test that threading lock exists for thread safety"""
    manager = ModelManager()

    assert hasattr(manager, '_lock')
    assert manager._lock is not None


@pytest.mark.unit
def test_model_manager_gpu_check():
    """Test GPU availability check runs without errors"""
    # This is called during init, so just verify it doesn't crash
    manager = ModelManager()
    # If we got here, GPU check completed successfully
    assert manager is not None


@pytest.mark.unit
def test_model_manager_initialization_with_custom_max_models():
    """Test initialization with custom max_loaded_models"""
    manager = ModelManager(max_loaded_models=5)
    assert manager.max_loaded_models == 5

    manager2 = ModelManager(max_loaded_models=1)
    assert manager2.max_loaded_models == 1


@pytest.mark.unit
def test_model_manager_processor_types():
    """Test that all processor types can be identified"""
    manager = ModelManager()

    # Get all models and check their types
    models = manager.get_available_models()
    valid_types = ['donut', 'florence', 'ocr', 'easyocr', 'paddle']

    for model in models:
        assert model['type'] in valid_types, f"Model {model['id']} has invalid type {model['type']}"


@pytest.mark.unit
def test_model_manager_processor_import_error_handling():
    """Test processor handles ImportError for missing dependencies"""
    manager = ModelManager()

    # Try to load a model that requires dependencies
    # This will raise ImportError if dependencies are missing
    try:
        # Try donut which requires torch/transformers
        donut_models = [m for m in manager.get_available_models() if m['type'] == 'donut']
        if donut_models:
            model_id = donut_models[0]['id']
            processor = manager.get_processor(model_id)
            # If successful, check it's not None
            assert processor is not None
    except ImportError as e:
        # Expected if torch/transformers not installed
        assert "torch" in str(e).lower() or "transformers" in str(e).lower()


@pytest.mark.unit
def test_model_manager_select_model_updates_current():
    """Test that selecting a model updates current_model"""
    manager = ModelManager()
    default_model = manager.get_default_model()

    result = manager.select_model(default_model)
    assert result is True
    assert manager.get_current_model() == default_model

    # Test selecting non-existent model
    result = manager.select_model('fake_model_xyz')
    assert result is False
    # Current model should not change
    assert manager.get_current_model() == default_model
