"""
Donut and Florence model processors for receipt extraction
"""
import os
os.environ.update({
    'TF_ENABLE_ONEDNN_OPTS': '0',
    'TF_CPP_MIN_LOG_LEVEL': '3',
    'TRANSFORMERS_VERBOSITY': 'error'
})

import sys
import json
import re
import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional
import torch
from transformers import DonutProcessor as TransformersDonutProcessor, VisionEncoderDecoderModel, AutoProcessor, AutoModelForCausalLM
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.data_structures import LineItem, ReceiptData, ExtractionResult
from utils.image_processing import load_and_validate_image, enhance_image

logger = logging.getLogger(__name__)

# Price validation
PRICE_MIN = 0
PRICE_MAX = 9999


class BaseDonutProcessor:
    """Base processor for Donut-based models"""

    def __init__(self, model_config: Dict):
        self.model_config = model_config
        self.model_id = model_config['huggingface_id']
        self.task_prompt = model_config['task_prompt']
        self.model_name = model_config['name']
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.processor = None
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the model and processor"""
        raise NotImplementedError("Subclasses must implement _load_model")

    def extract(self, image_path: str) -> ExtractionResult:
        """Extract receipt data from image"""
        raise NotImplementedError("Subclasses must implement extract")

    @staticmethod
    def normalize_price(value) -> Optional[Decimal]:
        """Normalize price values"""
        if value is None:
            return None
        try:
            price_str = str(value).replace('$', '').replace(',', '').strip()
            if price_str.startswith('-') or re.match(r'^\d{5}(-?\d{4})?$', price_str):
                return None
            val = Decimal(price_str)
            return val if PRICE_MIN <= val <= PRICE_MAX else None
        except (ValueError, ArithmeticError):
            return None

    @staticmethod
    def parse_json_output(json_str: str) -> Dict:
        """Parse JSON from model output"""
        if not json_str or not json_str.strip():
            logger.warning("Empty output from model")
            return {}

        try:
            json_str = json_str.strip()
            # Remove markdown code blocks if present
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse as direct JSON: {e}")
            # Try to extract JSON from text
            try:
                match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if match:
                    extracted = match.group(0)
                    logger.info(f"Attempting to parse extracted JSON: {extracted[:100]}...")
                    return json.loads(extracted)
                else:
                    logger.warning("No JSON object found in output")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to extract JSON from text: {e}")
        return {}


class DonutProcessor(BaseDonutProcessor):
    """Processor for Donut models (SROIE, CORD, etc.)"""

    def _load_model(self):
        """Load Donut model"""
        logger.info(f"Loading Donut model: {self.model_id}")
        try:
            self.processor = TransformersDonutProcessor.from_pretrained(self.model_id)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_id)
            self.model.to(self.device)

            # Log model configuration
            logger.info(f"Model loaded on {self.device}")
            logger.info(f"Model max length: {self.model.decoder.config.max_position_embeddings}")
            logger.info(f"Task prompt: {self.task_prompt}")
            logger.info(f"Tokenizer vocab size: {len(self.processor.tokenizer)}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def extract(self, image_path: str) -> ExtractionResult:
        """Extract receipt data using Donut model"""
        start_time = time.time()

        try:
            # Load and preprocess image
            image = load_and_validate_image(image_path)
            image = enhance_image(image)

            # Prepare inputs
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)

            # Generate output
            task_prompt = self.task_prompt
            decoder_input_ids = self.processor.tokenizer(
                task_prompt,
                add_special_tokens=False,
                return_tensors="pt"
            ).input_ids.to(self.device)

            outputs = self.model.generate(
                pixel_values,
                decoder_input_ids=decoder_input_ids,
                max_length=self.model.decoder.config.max_position_embeddings,
                early_stopping=True,
                pad_token_id=self.processor.tokenizer.pad_token_id,
                eos_token_id=self.processor.tokenizer.eos_token_id,
                use_cache=True,
                num_beams=1,
                bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                return_dict_in_generate=True,
            )

            # Decode output
            sequence = self.processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(self.processor.tokenizer.eos_token, "").replace(
                self.processor.tokenizer.pad_token, ""
            )
            sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()

            # Debug logging
            logger.info(f"Raw model output: {sequence}")

            # Parse JSON output
            parsed_data = self.parse_json_output(sequence)
            logger.info(f"Parsed data: {parsed_data}")

            # Check if parsing was successful
            if not parsed_data:
                logger.warning("Model output could not be parsed as JSON")
                logger.warning(f"Raw sequence was: {sequence[:200]}...")  # Log first 200 chars

                # Try fallback text extraction for SROIE and CORD models
                if sequence:
                    if 'sroie' in self.model_id.lower():
                        logger.info("Attempting fallback text extraction from plain text output (SROIE)")
                        parsed_data = self._extract_from_text(sequence)
                        if parsed_data:
                            logger.info(f"Fallback extraction found: {parsed_data}")
                    elif 'cord' in self.model_id.lower():
                        logger.info("Attempting fallback text extraction from plain text output (CORD)")
                        parsed_data = self._extract_from_text_cord(sequence)
                        if parsed_data:
                            logger.info(f"Fallback extraction found: {parsed_data}")

            # Build ReceiptData
            receipt = self._build_receipt_data(parsed_data)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name

            # Add diagnostic note if no data was extracted
            if not parsed_data:
                receipt.extraction_notes.append("Model produced no parseable output")
            elif sequence and not self.parse_json_output(sequence):
                # Model produced text instead of JSON - we used fallback
                if 'sroie' in self.model_id.lower() or 'cord' in self.model_id.lower():
                    receipt.extraction_notes.append("Model produced plain text instead of JSON - used fallback extraction")
            elif not any([receipt.store_name, receipt.store_address, receipt.total, receipt.transaction_date, receipt.items]):
                receipt.extraction_notes.append("Model output parsed but no fields matched expected format")

            # Calculate confidence score
            receipt.confidence_score = self._calculate_confidence(receipt)

            return ExtractionResult(success=True, data=receipt)

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractionResult(success=False, error=str(e))

    def _build_receipt_data(self, parsed_data: Dict) -> ReceiptData:
        """Build ReceiptData from parsed JSON"""
        receipt = ReceiptData()

        # Extract basic fields
        receipt.store_name = parsed_data.get('company') or parsed_data.get('store_name')
        receipt.store_address = parsed_data.get('address')
        receipt.transaction_date = parsed_data.get('date')

        # Extract total
        total_str = parsed_data.get('total')
        if total_str:
            receipt.total = self.normalize_price(total_str)

        # Extract items if available
        items_data = parsed_data.get('menu', []) or parsed_data.get('items', [])
        for item_data in items_data:
            if isinstance(item_data, dict):
                name = item_data.get('nm') or item_data.get('name')
                price = item_data.get('price') or item_data.get('total_price')

                if name and price:
                    normalized_price = self.normalize_price(price)
                    if normalized_price:
                        receipt.items.append(LineItem(
                            name=name,
                            total_price=normalized_price
                        ))

        return receipt

    def _extract_from_text(self, text: str) -> Dict:
        """
        Fallback: Extract structured data from plain text when JSON parsing fails.
        This handles cases where SROIE model outputs text instead of JSON.
        """
        extracted = {}

        # Clean up text - remove special tokens and weird characters
        text = re.sub(r'[歲嵗的]', '', text)  # Remove garbled unicode
        text = re.sub(r'</?s_\w+>', '', text)  # Remove special tokens like </s_address>

        # Extract total (look for common patterns like "TOTAL 12.34" or just prices)
        total_patterns = [
            r'total[:\s]*\$?(\d+[.,]\d{2})',
            r'(?:^|\s)(\d+[.,]\d{2})\s*$',  # Last price on line
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['total'] = match.group(1).replace(',', '.')
                break

        # Extract date (various formats)
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                extracted['date'] = match.group(1)
                break

        # Extract address (look for ZIP code and surrounding text)
        address_match = re.search(r'([A-Z\s]+(?:TX|CA|NY|FL)[,\s]*\d{5}(?:-\d{4})?)', text)
        if address_match:
            extracted['address'] = address_match.group(1).strip()

        # Extract store/company name (look for "STORE" or uppercase words at start)
        store_patterns = [
            r'(?:STORE|SHOP|MARKET)\s*#?\d+\s*-?\s*([A-Z\s]+)',
            r'^([A-Z][A-Z\s]{2,20}?)(?:\s+\d|\s+[A-Z]{2}\s+\d)',  # Uppercase words before address
        ]
        for pattern in store_patterns:
            match = re.search(pattern, text)
            if match:
                extracted['company'] = match.group(1).strip()
                break

        # If we found address but no company, try to extract from beginning
        if 'address' in extracted and 'company' not in extracted:
            # Text before address might be company name
            addr_pos = text.find(extracted['address'])
            if addr_pos > 0:
                before_addr = text[:addr_pos].strip()
                # Take last uppercase sequence before address
                company_match = re.search(r'([A-Z][A-Z\s]{2,30})$', before_addr)
                if company_match:
                    extracted['company'] = company_match.group(1).strip()

        return extracted

    def _extract_from_text_cord(self, text: str) -> Dict:
        """
        Fallback: Extract structured data from plain text for CORD models.
        CORD models are trained to extract more complex receipt data including line items.
        """
        extracted = {}

        # Clean up text - remove special tokens
        text = re.sub(r'</?s_\w+>', '', text)  # Remove special tokens like </s_cord-v2>
        text = re.sub(r'[歲嵗的]', '', text)  # Remove garbled unicode

        # Extract store/company name (usually at the beginning)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # First meaningful line is usually the store name
            for line in lines[:3]:
                if len(line) > 2 and not re.match(r'^\d+[.,]\d{2}$', line):
                    extracted['company'] = line
                    break

        # Extract total (look for common patterns)
        total_patterns = [
            r'(?:total|grand total|amount)[:\s]*\$?(\d+[.,]\d{2})',
            r'(?:^|\n)total[:\s]*(\d+[.,]\d{2})',
            r'(?:^|\s)(\d+[.,]\d{2})\s*$',  # Last price on line
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['total'] = match.group(1).replace(',', '.')
                break

        # Extract date (various formats)
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(\d{2}/\d{2}/\d{4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                extracted['date'] = match.group(1)
                break

        # Extract address (look for ZIP code and surrounding text)
        address_patterns = [
            r'([A-Z\s]+(?:TX|CA|NY|FL|WA|IL|MA|PA|OH)[,\s]*\d{5}(?:-\d{4})?)',
            r'(\d+\s+[A-Z][a-z]+\s+(?:St|Ave|Rd|Blvd|Lane|Drive|Street|Avenue))',
        ]
        for pattern in address_patterns:
            match = re.search(pattern, text)
            if match:
                extracted['address'] = match.group(1).strip()
                break

        # Extract menu items (CORD specific)
        # Look for patterns like "Item Name 2.99" or "Item Name x2 5.98"
        menu_items = []
        item_patterns = [
            r'([A-Za-z\s]{3,30})\s+(?:x\d+\s+)?\$?(\d+[.,]\d{2})',
            r'([A-Za-z][A-Za-z\s]{2,30}?)\s+(\d+[.,]\d{2})',
        ]

        for line in lines:
            # Skip lines that are likely headers or totals
            line_lower = line.lower()
            if any(word in line_lower for word in ['total', 'subtotal', 'tax', 'change', 'cash', 'card']):
                continue

            for pattern in item_patterns:
                match = re.search(pattern, line)
                if match:
                    item_name = match.group(1).strip()
                    item_price = match.group(2).replace(',', '.')

                    # Validate item name and price
                    if len(item_name) >= 3 and len(item_name) <= 50:
                        try:
                            price_val = float(item_price)
                            if 0 < price_val < 1000:  # Reasonable price range
                                menu_items.append({
                                    'nm': item_name,
                                    'price': item_price
                                })
                        except ValueError:
                            pass
                    break

        if menu_items:
            extracted['menu'] = menu_items

        return extracted

    def _calculate_confidence(self, receipt: ReceiptData) -> float:
        """Calculate confidence score based on extracted fields"""
        score = 0.0

        # For SROIE model (basic field extraction)
        if 'sroie' in self.model_id.lower():
            if receipt.store_name:
                score += 30
            if receipt.total:
                score += 30
            if receipt.store_address:
                score += 20
            if receipt.transaction_date:
                score += 20
            return min(100.0, score)

        # For models with item extraction (CORD, etc.)
        if receipt.items:
            # Items: up to 45 points (4.5 per item, max 10 items)
            score += min(45, len(receipt.items) * 4.5)
        if receipt.store_name:
            score += 15
        if receipt.total:
            score += 25
            # Coverage bonus if items exist
            if receipt.items:
                try:
                    items_sum = sum(item.total_price for item in receipt.items)
                    coverage = (items_sum / receipt.total * 100) if receipt.total > 0 else 0
                    if 95 <= coverage <= 105:
                        score += 15  # Perfect coverage
                    elif 85 <= coverage <= 115:
                        score += 10  # Good coverage
                except (ValueError, ArithmeticError):
                    pass
        if receipt.transaction_date:
            score += 5

        return min(100.0, score)


class FlorenceProcessor(BaseDonutProcessor):
    """Processor for Microsoft Florence-2 model"""

    def _load_model(self):
        """Load Florence-2 model"""
        logger.info(f"Loading Florence-2 model: {self.model_id}")
        try:
            # Load model with explicit attention implementation to avoid SDPA errors
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                trust_remote_code=True,
                attn_implementation="eager"  # Explicitly use eager attention to avoid _supports_sdpa error
            )
            self.processor = AutoProcessor.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )
            self.model.to(self.device)
            logger.info(f"Model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def extract(self, image_path: str) -> ExtractionResult:
        """Extract receipt data using Florence-2"""
        start_time = time.time()

        try:
            # Load image
            image = load_and_validate_image(image_path)

            # Run OCR with region detection
            inputs = self.processor(
                text=self.task_prompt,
                images=image,
                return_tensors="pt"
            ).to(self.device)

            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=1024,
                num_beams=3,
            )

            generated_text = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=False
            )[0]

            # Parse Florence output
            parsed_output = self.processor.post_process_generation(
                generated_text,
                task=self.task_prompt,
                image_size=(image.width, image.height)
            )

            # Build receipt data from OCR results
            receipt = self._build_receipt_from_ocr(parsed_output)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name

            return ExtractionResult(success=True, data=receipt)

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractionResult(success=False, error=str(e))

    def _build_receipt_from_ocr(self, parsed_output: Dict) -> ReceiptData:
        """Build ReceiptData from Florence OCR output"""
        receipt = ReceiptData()

        # Extract text regions
        ocr_result = parsed_output.get(self.task_prompt, {})
        texts = ocr_result.get('labels', [])

        # Simple heuristic parsing (can be improved)
        all_text = ' '.join(texts)

        # Extract total
        total_pattern = r'total[:\s]*\$?(\d+\.\d{2})'
        total_match = re.search(total_pattern, all_text, re.IGNORECASE)
        if total_match:
            receipt.total = self.normalize_price(total_match.group(1))

        # Extract date
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        date_match = re.search(date_pattern, all_text)
        if date_match:
            receipt.transaction_date = date_match.group(1)

        # Store name (first non-empty line typically)
        if texts:
            receipt.store_name = texts[0]

        receipt.extraction_notes.append("Basic Florence-2 OCR extraction")

        return receipt
