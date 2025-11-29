"""
Tests for model_trainer.py - ModelTrainer, DataAugmenter, IncrementalModelDevelopment
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np


class TestModelTrainer:
    """Tests for ModelTrainer class"""
    
    def test_model_trainer_initialization(self):
        """Test ModelTrainer initialization"""
        from shared.models.model_trainer import ModelTrainer
        
        config = {'param1': 'value1', 'param2': 'value2'}
        trainer = ModelTrainer('test_model', config)
        
        assert trainer.model_type == 'test_model'
        assert trainer.config == config
        assert trainer.training_data == []
        assert trainer.validation_data == []
    
    def test_add_training_sample(self):
        """Test adding training samples"""
        from shared.models.model_trainer import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        trainer.add_training_sample('/path/to/image.jpg', {'store': 'Test Store', 'total': 25.00})
        
        assert len(trainer.training_data) == 1
        assert trainer.training_data[0]['image'] == '/path/to/image.jpg'
        assert trainer.training_data[0]['truth']['store'] == 'Test Store'
    
    def test_add_validation_sample(self):
        """Test adding validation samples"""
        from shared.models.model_trainer import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        trainer.add_validation_sample('/path/to/image.jpg', {'store': 'Test Store'})
        
        assert len(trainer.validation_data) == 1
        assert trainer.validation_data[0]['image'] == '/path/to/image.jpg'
    
    def test_fine_tune_paddle_with_data(self):
        """Test fine_tune_paddle with training data"""
        from shared.models.model_trainer import ModelTrainer
        
        trainer = ModelTrainer('paddle', {})
        trainer.add_training_sample('/path/to/image.jpg', {'total': 25.00})
        
        # Should not raise error when data exists
        trainer.fine_tune_paddle(epochs=3, batch_size=4)
    
    def test_fine_tune_paddle_without_data(self):
        """Test fine_tune_paddle without data raises error"""
        from shared.models.model_trainer import ModelTrainer
        
        trainer = ModelTrainer('paddle', {})
        
        with pytest.raises(ValueError, match="No training data provided"):
            trainer.fine_tune_paddle()
    
    def test_evaluate_model_with_data(self):
        """Test evaluate_model with validation data"""
        from shared.models.model_trainer import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        trainer.add_validation_sample('/path/to/image.jpg', {'total': 25.00})
        
        results = trainer.evaluate_model()
        
        assert 'accuracy' in results
        assert 'precision' in results
        assert 'recall' in results
    
    def test_evaluate_model_without_data(self):
        """Test evaluate_model without validation data returns empty dict"""
        from shared.models.model_trainer import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        results = trainer.evaluate_model()
        
        assert results == {}
    
    def test_save_model(self):
        """Test save_model creates file"""
        from shared.models.model_trainer import ModelTrainer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = ModelTrainer('test_model', {'key': 'value'})
            trainer.add_training_sample('/path/to/image.jpg', {'total': 25.00})
            
            output_path = os.path.join(tmpdir, 'models', 'model.json')
            trainer.save_model(output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert data['type'] == 'test_model'
            assert data['config'] == {'key': 'value'}
            assert data['samples'] == 1
    
    def test_incremental_learn(self):
        """Test incremental_learn adds corrections to training data"""
        from shared.models.model_trainer import ModelTrainer
        
        trainer = ModelTrainer('test_model', {})
        
        feedback = {
            'correction_type': 'total_fix',
            'corrections': [
                {'field': 'total', 'old': 25.00, 'new': 30.00},
                {'field': 'store', 'old': 'Store A', 'new': 'Store B'}
            ]
        }
        
        trainer.incremental_learn(feedback)
        
        assert len(trainer.training_data) == 2


class TestDataAugmenter:
    """Tests for DataAugmenter class"""
    
    @pytest.mark.skipif(not pytest.importorskip("cv2", reason="cv2 not installed"), reason="cv2 required")
    def test_augment_image(self):
        """Test augment_image generates augmented images"""
        from shared.models.model_trainer import DataAugmenter
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image
            img = Image.new('RGB', (100, 100), color='white')
            input_path = os.path.join(tmpdir, 'test_image.png')
            img.save(input_path)
            
            # Augment the image
            output_dir = os.path.join(tmpdir, 'augmented')
            os.makedirs(output_dir)
            
            result = DataAugmenter.augment_image(input_path, output_dir)
            
            # Should generate 8 augmented images (4 rotations + 4 brightness)
            assert len(result) == 8
            
            # Verify all files exist
            for path in result:
                assert os.path.exists(path)


class TestIncrementalModelDevelopment:
    """Tests for IncrementalModelDevelopment class"""
    
    def test_initialization(self):
        """Test initialization"""
        from shared.models.model_trainer import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model_v1')
        
        assert dev.base_model_id == 'base_model_v1'
        assert dev.iterations == []
        assert dev.performance_history == []
    
    def test_create_iteration(self):
        """Test creating iterations"""
        from shared.models.model_trainer import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        
        iteration_id = dev.create_iteration('First iteration', {'learning_rate': 0.001})
        
        assert iteration_id == 'base_model_v1'
        assert len(dev.iterations) == 1
        assert dev.iterations[0]['name'] == 'First iteration'
        
        iteration_id2 = dev.create_iteration('Second iteration', {'learning_rate': 0.0005})
        assert iteration_id2 == 'base_model_v2'
    
    def test_log_performance(self):
        """Test logging performance metrics"""
        from shared.models.model_trainer import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        dev.create_iteration('Test', {})
        
        dev.log_performance('base_model_v1', {'accuracy': 0.85, 'loss': 0.15})
        
        assert len(dev.performance_history) == 1
        assert dev.performance_history[0]['metrics']['accuracy'] == 0.85
    
    def test_get_best_iteration_with_data(self):
        """Test getting best iteration"""
        from shared.models.model_trainer import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        dev.create_iteration('v1', {})
        dev.create_iteration('v2', {})
        
        dev.log_performance('base_model_v1', {'accuracy': 0.80})
        dev.log_performance('base_model_v2', {'accuracy': 0.90})
        
        best = dev.get_best_iteration()
        assert best == 'base_model_v2'
    
    def test_get_best_iteration_empty(self):
        """Test getting best iteration with no data"""
        from shared.models.model_trainer import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        assert dev.get_best_iteration() is None
    
    def test_export_iteration(self):
        """Test exporting an iteration"""
        from shared.models.model_trainer import IncrementalModelDevelopment
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dev = IncrementalModelDevelopment('base_model')
            dev.create_iteration('Test iteration', {'param': 'value'})
            
            output_path = os.path.join(tmpdir, 'iteration.json')
            dev.export_iteration('base_model_v1', output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert data['name'] == 'Test iteration'
    
    def test_export_iteration_not_found(self):
        """Test exporting non-existent iteration raises error"""
        from shared.models.model_trainer import IncrementalModelDevelopment
        
        dev = IncrementalModelDevelopment('base_model')
        
        with pytest.raises(ValueError, match="not found"):
            dev.export_iteration('nonexistent_v1', '/tmp/output.json')
