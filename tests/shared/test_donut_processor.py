import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from decimal import Decimal
import json


@pytest.fixture
def donut_config():
    """Configuration for Donut processor"""
    return {
        'id': 'donut_sroie',
        'name': 'Donut SROIE',
        'type': 'donut',
        'description': 'Donut model for SROIE',
        'huggingface_id': 'naver-clova-ix/donut-base-finetuned-cord-v2',
        'task_prompt': '<s_cord-v2>'
    }


@pytest.fixture
def florence_config():
    """Configuration for Florence processor"""
    return {
        'id': 'florence2',
        'name': 'Florence-2',
        'type': 'florence',
        'description': 'Florence-2 model',
        'huggingface_id': 'microsoft/Florence-2-large',
        'task_prompt': '<OCR_WITH_REGION>'
    }


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.TransformersDonutProcessor')
@patch('shared.models.donut_processor.VisionEncoderDecoderModel')
@patch('shared.models.donut_processor.load_and_validate_image')
@patch('shared.models.donut_processor.enhance_image')
def test_donut_processor_initialization(mock_enhance, mock_load, mock_model_cls, mock_proc_cls, mock_torch, donut_config):
    """Test DonutProcessor initialization"""
    from shared.models.donut_processor import DonutProcessor

    mock_torch.cuda.is_available.return_value = False
    mock_processor = Mock()
    mock_model = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls.from_pretrained.return_value = mock_model

    processor = DonutProcessor(donut_config)

    assert processor.model_config == donut_config
    assert processor.model_id == 'naver-clova-ix/donut-base-finetuned-cord-v2'
    assert processor.task_prompt == '<s_cord-v2>'
    assert processor.model_name == 'Donut SROIE'
    assert processor.device == 'cpu'
    assert processor.processor == mock_processor
    assert processor.model == mock_model


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.TransformersDonutProcessor')
@patch('shared.models.donut_processor.VisionEncoderDecoderModel')
def test_donut_processor_gpu_detection(mock_model_cls, mock_proc_cls, mock_torch, donut_config):
    """Test GPU detection and device assignment"""
    from shared.models.donut_processor import DonutProcessor

    mock_torch.cuda.is_available.return_value = True
    mock_processor = Mock()
    mock_model = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls.from_pretrained.return_value = mock_model

    processor = DonutProcessor(donut_config)

    assert processor.device == 'cuda'
    mock_model.to.assert_called_with('cuda')


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.TransformersDonutProcessor')
@patch('shared.models.donut_processor.VisionEncoderDecoderModel')
def test_donut_processor_load_retry(mock_model_cls, mock_proc_cls, mock_torch, donut_config):
    """Test model loading with retry logic"""
    from shared.models.donut_processor import DonutProcessor

    mock_torch.cuda.is_available.return_value = False

    # First attempt fails, second succeeds
    mock_model_cls.from_pretrained.side_effect = [
        RuntimeError("Download failed"),
        Mock()
    ]
    mock_proc_cls.from_pretrained.side_effect = [
        RuntimeError("Download failed"),
        Mock()
    ]

    with patch('time.sleep'):  # Don't actually sleep in tests
        processor = DonutProcessor(donut_config)

    # Should succeed after retry
    assert processor.model is not None


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.TransformersDonutProcessor')
@patch('shared.models.donut_processor.VisionEncoderDecoderModel')
@patch('time.sleep')
def test_donut_processor_load_failure(mock_sleep, mock_model_cls, mock_proc_cls, mock_torch, donut_config):
    """Test model loading fails after max retries"""
    from shared.models.donut_processor import DonutProcessor

    mock_torch.cuda.is_available.return_value = False
    mock_model_cls.from_pretrained.side_effect = RuntimeError("Network error")
    mock_proc_cls.from_pretrained.side_effect = RuntimeError("Network error")

    with pytest.raises(RuntimeError) as exc_info:
        processor = DonutProcessor(donut_config)

    assert "Failed to load" in str(exc_info.value)
    assert "after 3 attempts" in str(exc_info.value)


@pytest.mark.unit
def test_normalize_price_valid():
    """Test price normalization with valid values"""
    from shared.models.donut_processor import BaseDonutProcessor

    assert BaseDonutProcessor.normalize_price('12.99') == Decimal('12.99')
    assert BaseDonutProcessor.normalize_price('$5.50') == Decimal('5.50')
    assert BaseDonutProcessor.normalize_price('100') == Decimal('100')
    assert BaseDonutProcessor.normalize_price('0.99') == Decimal('0.99')
    assert BaseDonutProcessor.normalize_price('1,234.56') == Decimal('1234.56')


@pytest.mark.unit
def test_normalize_price_invalid():
    """Test price normalization with invalid values"""
    from shared.models.donut_processor import BaseDonutProcessor

    assert BaseDonutProcessor.normalize_price(None) is None
    assert BaseDonutProcessor.normalize_price('') is None
    assert BaseDonutProcessor.normalize_price('-5.00') is None
    assert BaseDonutProcessor.normalize_price('abc') is None
    assert BaseDonutProcessor.normalize_price('10000') is None  # Out of range
    assert BaseDonutProcessor.normalize_price('12345') is None  # Looks like zip code


@pytest.mark.unit
def test_parse_json_output_valid():
    """Test parsing valid JSON output"""
    from shared.models.donut_processor import BaseDonutProcessor

    test_cases = [
        ('{"store": "Test"}', {"store": "Test"}),
        ('```json\n{"store": "Test"}\n```', {"store": "Test"}),
        ('Some text {"store": "Test"} more text', {"store": "Test"}),
    ]

    for input_str, expected in test_cases:
        result = BaseDonutProcessor.parse_json_output(input_str)
        assert result == expected


@pytest.mark.unit
def test_parse_json_output_invalid():
    """Test parsing invalid JSON output"""
    from shared.models.donut_processor import BaseDonutProcessor

    test_cases = [
        '',
        '   ',
        'Not JSON at all',
        'Almost {JSON but not quite',
    ]

    for input_str in test_cases:
        result = BaseDonutProcessor.parse_json_output(input_str)
        assert result == {}


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.TransformersDonutProcessor')
@patch('shared.models.donut_processor.VisionEncoderDecoderModel')
@patch('shared.models.donut_processor.load_and_validate_image')
@patch('shared.models.donut_processor.enhance_image')
def test_donut_extract_success(mock_enhance, mock_load, mock_model_cls, mock_proc_cls, mock_torch, donut_config):
    """Test successful extraction with Donut"""
    from shared.models.donut_processor import DonutProcessor
    from PIL import Image

    mock_torch.cuda.is_available.return_value = False

    # Mock image
    mock_image = Mock(spec=Image.Image)
    mock_load.return_value = mock_image
    mock_enhance.return_value = mock_image

    # Mock processor and model
    mock_processor = Mock()
    mock_model = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls.from_pretrained.return_value = mock_model

    # Mock tokenizer
    mock_tokenizer = Mock()
    mock_tokenizer.pad_token_id = 0
    mock_tokenizer.eos_token_id = 2
    mock_tokenizer.eos_token = '</s>'
    mock_tokenizer.pad_token = '<pad>'
    mock_tokenizer.unk_token_id = 3
    mock_tokenizer.return_value = Mock(input_ids=Mock(to=Mock(return_value=Mock())))
    mock_processor.tokenizer = mock_tokenizer

    # Mock image processing
    mock_processor.return_value = Mock(pixel_values=Mock(to=Mock(return_value=Mock())))

    # Mock model config
    mock_decoder_config = Mock()
    mock_decoder_config.max_position_embeddings = 1024
    mock_model.decoder.config = mock_decoder_config

    # Mock generation output
    mock_output = Mock()
    mock_output.sequences = [Mock()]
    mock_model.generate.return_value = mock_output

    # Mock JSON output
    json_output = json.dumps({
        'company': 'Test Store',
        'address': '123 Main St',
        'date': '2024-01-15',
        'total': '12.99',
        'menu': [
            {'nm': 'Item 1', 'price': '5.99'},
            {'nm': 'Item 2', 'price': '6.00'}
        ]
    })
    mock_processor.batch_decode.return_value = [f'<s_cord-v2>{json_output}</s>']

    processor = DonutProcessor(donut_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    assert result.data is not None
    assert result.data.store_name == 'Test Store'
    assert result.data.store_address == '123 Main St'
    assert result.data.transaction_date == '2024-01-15'
    assert result.data.total == Decimal('12.99')
    assert len(result.data.items) == 2


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.TransformersDonutProcessor')
@patch('shared.models.donut_processor.VisionEncoderDecoderModel')
@patch('shared.models.donut_processor.load_and_validate_image')
@patch('shared.models.donut_processor.enhance_image')
def test_donut_extract_fallback_text(mock_enhance, mock_load, mock_model_cls, mock_proc_cls, mock_torch, donut_config):
    """Test extraction with fallback text parsing for SROIE"""
    from shared.models.donut_processor import DonutProcessor
    from PIL import Image

    mock_torch.cuda.is_available.return_value = False

    mock_image = Mock(spec=Image.Image)
    mock_load.return_value = mock_image
    mock_enhance.return_value = mock_image

    mock_processor = Mock()
    mock_model = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls.from_pretrained.return_value = mock_model

    mock_tokenizer = Mock()
    mock_tokenizer.pad_token_id = 0
    mock_tokenizer.eos_token_id = 2
    mock_tokenizer.eos_token = '</s>'
    mock_tokenizer.pad_token = '<pad>'
    mock_tokenizer.unk_token_id = 3
    mock_tokenizer.return_value = Mock(input_ids=Mock(to=Mock(return_value=Mock())))
    mock_processor.tokenizer = mock_tokenizer

    mock_processor.return_value = Mock(pixel_values=Mock(to=Mock(return_value=Mock())))

    mock_decoder_config = Mock()
    mock_decoder_config.max_position_embeddings = 1024
    mock_model.decoder.config = mock_decoder_config

    mock_output = Mock()
    mock_output.sequences = [Mock()]
    mock_model.generate.return_value = mock_output

    # Return plain text instead of JSON
    text_output = """Test Store
123 Main St
Date: 01/15/2024
Total: $12.99"""
    mock_processor.batch_decode.return_value = [f'<s_sroie>{text_output}</s>']

    processor = DonutProcessor(donut_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is True
    # Should extract some data from text
    assert result.data is not None


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.TransformersDonutProcessor')
@patch('shared.models.donut_processor.VisionEncoderDecoderModel')
@patch('shared.models.donut_processor.load_and_validate_image')
def test_donut_extract_exception(mock_load, mock_model_cls, mock_proc_cls, mock_torch, donut_config):
    """Test extraction handles exceptions"""
    from shared.models.donut_processor import DonutProcessor

    mock_torch.cuda.is_available.return_value = False
    mock_processor = Mock()
    mock_model = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls.from_pretrained.return_value = mock_model

    mock_load.side_effect = RuntimeError("Image load failed")

    processor = DonutProcessor(donut_config)
    result = processor.extract('/path/to/test/image.jpg')

    assert result.success is False
    assert "Image load failed" in result.error


@pytest.mark.unit
def test_safe_extract_string():
    """Test safe string extraction from various data types"""
    from shared.models.donut_processor import DonutProcessor
    from shared.models.donut_processor import BaseDonutProcessor
    from unittest.mock import MagicMock

    # Create a mock processor instance just for testing the method
    processor = MagicMock(spec=BaseDonutProcessor)
    # Bind the actual method to the mock
    processor._safe_extract_string = BaseDonutProcessor._safe_extract_string.__get__(processor)

    # Test cases
    assert processor._safe_extract_string(None) is None
    assert processor._safe_extract_string('') is None
    assert processor._safe_extract_string('  ') is None
    assert processor._safe_extract_string('test') == 'test'
    assert processor._safe_extract_string('  test  ') == 'test'
    assert processor._safe_extract_string(123) == '123'
    assert processor._safe_extract_string(45.67) == '45.67'
    assert processor._safe_extract_string({'nm': 'test'}) == 'test'
    assert processor._safe_extract_string({'name': 'test'}) == 'test'
    assert processor._safe_extract_string({'price': '5.99'}) == '5.99'
    assert processor._safe_extract_string({'other': 'value'}) == 'value'


@pytest.mark.unit
def test_calculate_confidence_sroie():
    """Test confidence calculation for SROIE model"""
    from shared.models.donut_processor import DonutProcessor
    from shared.utils.data_structures import ReceiptData
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor.model_id = 'donut-sroie'
    processor._calculate_confidence = DonutProcessor._calculate_confidence.__get__(processor)

    receipt = ReceiptData()
    assert processor._calculate_confidence(receipt) == 0.0

    receipt.store_name = "Test Store"
    assert processor._calculate_confidence(receipt) == 30.0

    receipt.total = Decimal('10.00')
    assert processor._calculate_confidence(receipt) == 60.0

    receipt.store_address = "123 Main St"
    assert processor._calculate_confidence(receipt) == 80.0

    receipt.transaction_date = "2024-01-15"
    assert processor._calculate_confidence(receipt) == 100.0


@pytest.mark.unit
def test_extract_from_text():
    """Test text extraction fallback"""
    from shared.models.donut_processor import DonutProcessor
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor._extract_from_text = DonutProcessor._extract_from_text.__get__(processor)

    text = """WALMART SUPERCENTER
123 Main Street, TX 12345
Date: 01/15/2024
Apple 2.99
Banana 1.49
Total: $4.48"""

    result = processor._extract_from_text(text)

    assert 'total' in result
    assert result['total'] == '4.48'
    assert 'date' in result
    assert result['date'] == '01/15/2024'


@pytest.mark.unit
def test_extract_from_text_cord():
    """Test CORD-specific text extraction"""
    from shared.models.donut_processor import DonutProcessor
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor._extract_from_text_cord = DonutProcessor._extract_from_text_cord.__get__(processor)

    text = """<s_nm>Test Store</s_nm>
<s_num>123 Main Street</s_num>
<s_total_price>$12.99</s_total_price>
<sep/>
<s_nm>Item 1</s_nm>
<s_price>5.99</s_price>
<s_cnt>1</s_cnt>
<sep/>
<s_nm>Item 2</s_nm>
<s_price>7.00</s_price>"""

    result = processor._extract_from_text_cord(text)

    assert result['company'] == 'Test Store'
    assert result['total'] == '12.99'
    assert 'menu' in result
    assert len(result['menu']) == 2


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.AutoProcessor')
@patch('shared.models.donut_processor.AutoModelForCausalLM')
def test_florence_processor_initialization(mock_model_cls, mock_proc_cls, mock_torch, florence_config):
    """Test FlorenceProcessor initialization"""
    from shared.models.donut_processor import FlorenceProcessor

    mock_torch.cuda.is_available.return_value = False
    mock_processor = Mock()
    mock_model = Mock()
    mock_proc_cls.from_pretrained.return_value = mock_processor
    mock_model_cls.from_pretrained.return_value = mock_model

    processor = FlorenceProcessor(florence_config)

    assert processor.model_config == florence_config
    assert processor.model_id == 'microsoft/Florence-2-large'
    assert processor.task_prompt == '<OCR_WITH_REGION>'
    assert processor.device == 'cpu'
    mock_model_cls.from_pretrained.assert_called_once()


@pytest.mark.unit
@patch('shared.models.donut_processor.torch')
@patch('shared.models.donut_processor.AutoProcessor')
@patch('shared.models.donut_processor.AutoModelForCausalLM')
@patch('time.sleep')
def test_florence_processor_load_failure(mock_sleep, mock_model_cls, mock_proc_cls, mock_torch, florence_config):
    """Test FlorenceProcessor loading fails after retries"""
    from shared.models.donut_processor import FlorenceProcessor

    mock_torch.cuda.is_available.return_value = False
    mock_model_cls.from_pretrained.side_effect = RuntimeError("Network error")

    with pytest.raises(RuntimeError) as exc_info:
        processor = FlorenceProcessor(florence_config)

    assert "Failed to load Florence-2" in str(exc_info.value)


@pytest.mark.unit
def test_build_receipt_data():
    """Test building receipt data from parsed JSON"""
    from shared.models.donut_processor import DonutProcessor
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor.normalize_price = DonutProcessor.normalize_price
    processor._safe_extract_string = DonutProcessor._safe_extract_string
    processor._build_receipt_data = DonutProcessor._build_receipt_data.__get__(processor)

    parsed_data = {
        'company': 'Test Store',
        'address': '123 Main St',
        'date': '2024-01-15',
        'total': '12.99',
        'menu': [
            {'nm': 'Item 1', 'price': '5.99'},
            {'nm': 'Item 2', 'price': '7.00'}
        ]
    }

    receipt = processor._build_receipt_data(parsed_data)

    assert receipt.store_name == 'Test Store'
    assert receipt.store_address == '123 Main St'
    assert receipt.transaction_date == '2024-01-15'
    assert receipt.total == Decimal('12.99')
    assert len(receipt.items) == 2
    assert receipt.items[0].name == 'Item 1'
    assert receipt.items[0].total_price == Decimal('5.99')


@pytest.mark.unit
def test_build_receipt_data_complex_total():
    """Test building receipt data with complex total structure"""
    from shared.models.donut_processor import DonutProcessor
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor.normalize_price = DonutProcessor.normalize_price
    processor._safe_extract_string = DonutProcessor._safe_extract_string
    processor._build_receipt_data = DonutProcessor._build_receipt_data.__get__(processor)

    parsed_data = {
        'company': 'Test Store',
        'total': {
            'total_price': '15.99',
            'cashprice': '20.00',
            'changeprice': '4.01'
        },
        'sub_total': {
            'subtotal_price': '14.50'
        }
    }

    receipt = processor._build_receipt_data(parsed_data)

    assert receipt.total == Decimal('15.99')
    assert receipt.cash_tendered == Decimal('20.00')
    assert receipt.change_given == Decimal('4.01')
    assert receipt.subtotal == Decimal('14.50')


@pytest.mark.unit
def test_build_receipt_data_alternate_fields():
    """Test building receipt data with alternate field names"""
    from shared.models.donut_processor import DonutProcessor
    from unittest.mock import MagicMock

    processor = MagicMock()
    processor.normalize_price = DonutProcessor.normalize_price
    processor._safe_extract_string = DonutProcessor._safe_extract_string
    processor._build_receipt_data = DonutProcessor._build_receipt_data.__get__(processor)

    parsed_data = {
        'store_name': 'Alternate Store',  # Using store_name instead of company
        'items': [  # Using items instead of menu
            {'name': 'Product A', 'total_price': '3.50'}
        ]
    }

    receipt = processor._build_receipt_data(parsed_data)

    assert receipt.store_name == 'Alternate Store'
    assert len(receipt.items) == 1
    assert receipt.items[0].name == 'Product A'
