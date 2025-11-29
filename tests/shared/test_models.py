"""
Test suite for shared.models.__init__.py
Tests the _get_processor_class lazy import functionality
"""
import pytest
from pathlib import Path
import sys

# Add shared to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))

from models import ModelManager, _get_processor_class


class TestModelManager:
    """Test ModelManager export"""

    def test_model_manager_import(self):
        """Test that ModelManager is exported"""
        assert ModelManager is not None


class TestGetProcessorClass:
    """Test _get_processor_class lazy import function"""

    def test_get_processor_class_invalid_type(self):
        """Test that invalid processor type raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            _get_processor_class('invalid_type')
        
        assert 'Unknown processor type' in str(exc_info.value)

    def test_get_processor_class_donut(self):
        """Test getting donut processor class"""
        try:
            processor_class = _get_processor_class('donut')
            assert processor_class is not None
            assert processor_class.__name__ == 'DonutProcessor'
        except ImportError:
            # torch not installed - expected in test environment
            pytest.skip("torch not installed")

    def test_get_processor_class_florence(self):
        """Test getting florence processor class"""
        try:
            processor_class = _get_processor_class('florence')
            assert processor_class is not None
            assert processor_class.__name__ == 'FlorenceProcessor'
        except ImportError:
            pytest.skip("torch not installed")

    def test_get_processor_class_ocr(self):
        """Test getting OCR processor class"""
        try:
            processor_class = _get_processor_class('ocr')
            assert processor_class is not None
            assert processor_class.__name__ == 'OCRProcessor'
        except ImportError:
            pytest.skip("pytesseract not installed")

    def test_get_processor_class_paddle(self):
        """Test getting paddle processor class"""
        try:
            processor_class = _get_processor_class('paddle')
            assert processor_class is not None
            assert processor_class.__name__ == 'PaddleProcessor'
        except ImportError:
            pytest.skip("paddleocr not installed")

    def test_get_processor_class_easyocr(self):
        """Test getting easyocr processor class"""
        try:
            processor_class = _get_processor_class('easyocr')
            assert processor_class is not None
            assert processor_class.__name__ == 'EasyOCRProcessor'
        except ImportError:
            pytest.skip("easyocr not installed")
"""
Test suite for Donut model finetuning
Tests coverage for shared/models/donut_finetuner.py
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add shared to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'shared'))


class TestReceiptDataset:
    """Test ReceiptDataset class"""

    @patch('models.donut_finetuner.Image')
    def test_dataset_length(self, mock_image):
        """Test dataset __len__ method"""
        try:
            from models.donut_finetuner import ReceiptDataset

            data = [
                {'image': 'image1.jpg', 'truth': {'total': 10.99}},
                {'image': 'image2.jpg', 'truth': {'total': 20.99}},
                {'image': 'image3.jpg', 'truth': {'total': 30.99}}
            ]

            mock_processor = Mock()
            dataset = ReceiptDataset(data, mock_processor)

            assert len(dataset) == 3
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")

    @patch('models.donut_finetuner.Image')
    def test_dataset_getitem(self, mock_image):
        """Test dataset __getitem__ method"""
        try:
            from models.donut_finetuner import ReceiptDataset
            import torch

            data = [{'image': 'test.jpg', 'truth': {'total': 25.99}}]

            # Mock processor
            mock_processor = Mock()
            mock_processor.return_value = Mock(
                pixel_values=torch.rand(1, 3, 224, 224)
            )
            mock_processor.tokenizer = Mock()
            mock_processor.tokenizer.return_value = Mock(
                input_ids=torch.randint(0, 100, (1, 512))
            )
            mock_processor.tokenizer.pad_token_id = 0

            # Mock image
            mock_img = Mock()
            mock_image.open.return_value = mock_img
            mock_img.convert.return_value = mock_img

            dataset = ReceiptDataset(data, mock_processor)
            item = dataset[0]

            assert 'pixel_values' in item
            assert 'labels' in item
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")


class TestDonutFinetuner:
    """Test DonutFinetuner class"""

    @patch('models.donut_finetuner.VisionEncoderDecoderModel')
    @patch('models.donut_finetuner.DonutProcessor')
    @patch('models.donut_finetuner.torch')
    def test_finetuner_initialization(self, mock_torch, mock_processor_class, mock_model_class):
        """Test DonutFinetuner initialization"""
        try:
            from models.donut_finetuner import DonutFinetuner

            # Mock CUDA availability
            mock_torch.cuda.is_available.return_value = False

            # Mock model and processor
            mock_model = Mock()
            mock_processor = Mock()
            mock_model_class.from_pretrained.return_value = mock_model
            mock_processor_class.from_pretrained.return_value = mock_processor

            finetuner = DonutFinetuner('donut_base')

            assert finetuner.model_id == 'donut_base'
            assert finetuner.device == 'cpu'
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")

    @patch('models.donut_finetuner.VisionEncoderDecoderModel')
    @patch('models.donut_finetuner.DonutProcessor')
    @patch('models.donut_finetuner.torch')
    def test_finetuner_cuda_detection(self, mock_torch, mock_processor_class, mock_model_class):
        """Test CUDA device detection"""
        try:
            from models.donut_finetuner import DonutFinetuner

            # Mock CUDA availability
            mock_torch.cuda.is_available.return_value = True

            mock_model = Mock()
            mock_processor = Mock()
            mock_model_class.from_pretrained.return_value = mock_model
            mock_processor_class.from_pretrained.return_value = mock_processor

            finetuner = DonutFinetuner('donut_base')

            assert finetuner.device == 'cuda'
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")

    @patch('models.donut_finetuner.VisionEncoderDecoderModel')
    @patch('models.donut_finetuner.DonutProcessor')
    @patch('models.donut_finetuner.torch')
    def test_finetuner_model_selection(self, mock_torch, mock_processor_class, mock_model_class):
        """Test model ID selection"""
        try:
            from models.donut_finetuner import DonutFinetuner

            mock_torch.cuda.is_available.return_value = False
            mock_model = Mock()
            mock_processor = Mock()
            mock_model_class.from_pretrained.return_value = mock_model
            mock_processor_class.from_pretrained.return_value = mock_processor

            # Test donut_cord
            finetuner = DonutFinetuner('donut_cord')
            mock_model_class.from_pretrained.assert_called_with('naver-clova-ix/donut-base-finetuned-cord-v2')

            # Test donut_base
            finetuner = DonutFinetuner('donut_base')
            mock_model_class.from_pretrained.assert_called_with('naver-clova-ix/donut-base')
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")

    @patch('models.donut_finetuner.VisionEncoderDecoderModel')
    @patch('models.donut_finetuner.DonutProcessor')
    @patch('models.donut_finetuner.torch')
    def test_finetuner_image_size_configuration(self, mock_torch, mock_processor_class, mock_model_class):
        """Test custom image size configuration"""
        try:
            from models.donut_finetuner import DonutFinetuner

            mock_torch.cuda.is_available.return_value = False
            mock_model = Mock()
            mock_processor = Mock()
            mock_processor.image_processor = Mock()
            mock_model_class.from_pretrained.return_value = mock_model
            mock_processor_class.from_pretrained.return_value = mock_processor

            custom_size = (1024, 768)
            finetuner = DonutFinetuner('donut_base', image_size=custom_size)

            assert finetuner.image_size == custom_size
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")


class TestDonutFinetunerTraining:
    """Test training-related functionality"""

    @patch('models.donut_finetuner.Seq2SeqTrainer')
    @patch('models.donut_finetuner.Seq2SeqTrainingArguments')
    @patch('models.donut_finetuner.VisionEncoderDecoderModel')
    @patch('models.donut_finetuner.DonutProcessor')
    @patch('models.donut_finetuner.torch')
    def test_train_method_exists(self, mock_torch, mock_processor_class, mock_model_class, mock_args, mock_trainer):
        """Test that train method can be called"""
        try:
            from models.donut_finetuner import DonutFinetuner

            mock_torch.cuda.is_available.return_value = False
            mock_model = Mock()
            mock_processor = Mock()
            mock_model_class.from_pretrained.return_value = mock_model
            mock_processor_class.from_pretrained.return_value = mock_processor

            finetuner = DonutFinetuner('donut_base')

            # Check method exists
            assert hasattr(finetuner, 'train')
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")


class TestDonutFinetunerSaving:
    """Test model saving functionality"""

    @patch('models.donut_finetuner.VisionEncoderDecoderModel')
    @patch('models.donut_finetuner.DonutProcessor')
    @patch('models.donut_finetuner.torch')
    def test_save_model_method_exists(self, mock_torch, mock_processor_class, mock_model_class):
        """Test that save_model method exists"""
        try:
            from models.donut_finetuner import DonutFinetuner

            mock_torch.cuda.is_available.return_value = False
            mock_model = Mock()
            mock_processor = Mock()
            mock_model_class.from_pretrained.return_value = mock_model
            mock_processor_class.from_pretrained.return_value = mock_processor

            finetuner = DonutFinetuner('donut_base')

            # Check method exists
            assert hasattr(finetuner, 'save_model')
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")


class TestDonutFinetunerErrorHandling:
    """Test error handling in DonutFinetuner"""

    @patch('models.donut_finetuner.VisionEncoderDecoderModel')
    @patch('models.donut_finetuner.DonutProcessor')
    @patch('models.donut_finetuner.torch')
    def test_model_loading_failure(self, mock_torch, mock_processor_class, mock_model_class):
        """Test handling of model loading failures"""
        try:
            from models.donut_finetuner import DonutFinetuner

            mock_torch.cuda.is_available.return_value = False

            # Make model loading fail
            mock_model_class.from_pretrained.side_effect = Exception("Model not found")

            # Should raise or handle exception
            with pytest.raises(Exception):
                finetuner = DonutFinetuner('donut_base')
        except ImportError:
            pytest.skip("Donut finetuner dependencies not available")
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
