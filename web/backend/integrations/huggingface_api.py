"""
=============================================================================
HUGGINGFACE INFERENCE API - Remote Model Inference
=============================================================================

Provides integration with HuggingFace Inference API for:
- Document text extraction using hosted models
- Model marketplace browsing
- Usage tracking and cost management

Environment Variables:
- HUGGINGFACE_API_KEY: HuggingFace API token

Usage:
    from integrations.huggingface_api import HuggingFaceInference
    
    hf = HuggingFaceInference()
    result = hf.extract_text(image_bytes, "naver-clova-ix/donut-base-finetuned-cord-v2")

=============================================================================
"""

import os
import logging
import base64
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import huggingface_hub
try:
    from huggingface_hub import InferenceClient, HfApi
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.warning("huggingface_hub not installed. Run: pip install huggingface-hub>=0.20.0")


@dataclass
class InferenceResult:
    """Result from HuggingFace Inference API."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    raw_text: Optional[str] = None
    model_id: str = ""
    processing_time: float = 0.0
    confidence: Optional[float] = None
    error: Optional[str] = None
    tokens_used: int = 0


@dataclass
class ModelInfo:
    """Information about a HuggingFace model."""
    model_id: str
    name: str
    description: str
    task: str
    downloads: int
    likes: int
    is_gated: bool
    requires_token: bool
    tags: List[str]


# Available models for receipt extraction
RECEIPT_EXTRACTION_MODELS = [
    {
        'id': 'naver-clova-ix/donut-base-finetuned-cord-v2',
        'name': 'Donut CORD v2',
        'description': 'Document understanding model fine-tuned on CORD dataset for receipt parsing',
        'task': 'document-question-answering',
        'recommended': True
    },
    {
        'id': 'microsoft/trocr-large-printed',
        'name': 'TrOCR Large',
        'description': 'Transformer-based OCR for printed text recognition',
        'task': 'image-to-text',
        'recommended': False
    },
    {
        'id': 'microsoft/Florence-2-large',
        'name': 'Florence 2 Large',
        'description': 'Foundation model for vision-language understanding',
        'task': 'image-to-text',
        'recommended': True
    },
    {
        'id': 'Salesforce/blip-image-captioning-large',
        'name': 'BLIP Large',
        'description': 'Image captioning and visual question answering',
        'task': 'image-to-text',
        'recommended': False
    }
]


class HuggingFaceInference:
    """
    HuggingFace Inference API client for receipt extraction.
    
    Supports multiple models and provides fallback mechanisms.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize HuggingFace Inference client.
        
        Args:
            api_key: HuggingFace API token (defaults to HUGGINGFACE_API_KEY env var)
        """
        if not HF_AVAILABLE:
            raise ImportError(
                "huggingface_hub required. Install with: pip install huggingface-hub>=0.20.0"
            )
        
        self.api_key = api_key or os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HUGGINGFACE_TOKEN')
        
        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not set. Some features may be limited.")
            self.client = InferenceClient()
        else:
            self.client = InferenceClient(token=self.api_key)
        
        self._request_count = 0
        self._last_request_time = 0
        
        logger.info("HuggingFaceInference initialized")
    
    def extract_text(
        self,
        image: Union[bytes, str],
        model_id: str = None,
        question: str = "Extract all text from this receipt including store name, items, prices, and total."
    ) -> InferenceResult:
        """
        Extract text from receipt image using HuggingFace model.
        
        Args:
            image: Image bytes or base64 string
            model_id: HuggingFace model ID (defaults to Donut CORD v2)
            question: Question for document QA models
            
        Returns:
            InferenceResult with extracted data
        """
        if model_id is None:
            model_id = 'naver-clova-ix/donut-base-finetuned-cord-v2'
        
        start_time = time.time()
        
        try:
            # Convert base64 to bytes if needed
            if isinstance(image, str):
                if image.startswith('data:'):
                    # Remove data URL prefix
                    image = image.split(',')[1]
                image = base64.b64decode(image)
            
            # Apply rate limiting
            self._rate_limit()
            
            # Call the appropriate API based on model type
            if 'donut' in model_id.lower():
                result = self._donut_extraction(image, model_id, question)
            else:
                result = self._generic_extraction(image, model_id)
            
            processing_time = time.time() - start_time
            self._request_count += 1
            
            return InferenceResult(
                success=True,
                data=result.get('data'),
                raw_text=result.get('raw_text'),
                model_id=model_id,
                processing_time=processing_time,
                confidence=result.get('confidence'),
                tokens_used=result.get('tokens_used', 0)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"HuggingFace inference error: {e}")
            
            return InferenceResult(
                success=False,
                model_id=model_id,
                processing_time=processing_time,
                error=str(e)
            )
    
    def _donut_extraction(
        self,
        image: bytes,
        model_id: str,
        question: str
    ) -> Dict[str, Any]:
        """Extract using Donut-style document QA model."""
        try:
            result = self.client.document_question_answering(
                image=image,
                question=question,
                model=model_id
            )
            
            # Parse Donut output
            if isinstance(result, list) and len(result) > 0:
                answer = result[0].get('answer', '')
                score = result[0].get('score', 0)
            else:
                answer = str(result)
                score = None
            
            return {
                'raw_text': answer,
                'data': self._parse_receipt_text(answer),
                'confidence': score
            }
            
        except Exception as e:
            logger.error(f"Donut extraction error: {e}")
            raise
    
    def _generic_extraction(
        self,
        image: bytes,
        model_id: str
    ) -> Dict[str, Any]:
        """Extract using generic image-to-text model."""
        try:
            result = self.client.image_to_text(
                image=image,
                model=model_id
            )
            
            if isinstance(result, str):
                text = result
            elif isinstance(result, list):
                text = result[0].get('generated_text', '') if result else ''
            else:
                text = str(result)
            
            return {
                'raw_text': text,
                'data': self._parse_receipt_text(text)
            }
            
        except Exception as e:
            logger.error(f"Generic extraction error: {e}")
            raise
    
    def _parse_receipt_text(self, text: str) -> Dict[str, Any]:
        """
        Parse extracted text into structured receipt data.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Structured receipt data
        """
        import re
        
        data = {
            'raw_text': text,
            'store': {},
            'items': [],
            'totals': {},
            'metadata': {}
        }
        
        lines = text.strip().split('\n')
        
        # Try to extract common patterns
        for line in lines:
            line = line.strip()
            
            # Look for total patterns
            total_match = re.search(r'(?:total|sum|amount)[:\s]*\$?(\d+\.?\d*)', line, re.IGNORECASE)
            if total_match:
                data['totals']['total'] = float(total_match.group(1))
            
            # Look for subtotal
            subtotal_match = re.search(r'(?:subtotal|sub-total)[:\s]*\$?(\d+\.?\d*)', line, re.IGNORECASE)
            if subtotal_match:
                data['totals']['subtotal'] = float(subtotal_match.group(1))
            
            # Look for tax
            tax_match = re.search(r'(?:tax|vat|gst)[:\s]*\$?(\d+\.?\d*)', line, re.IGNORECASE)
            if tax_match:
                data['totals']['tax'] = float(tax_match.group(1))
            
            # Look for date patterns
            date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', line)
            if date_match and 'date' not in data['metadata']:
                data['metadata']['date'] = date_match.group(1)
            
            # Look for item patterns (name and price)
            item_match = re.search(r'(.+?)\s+\$?(\d+\.?\d*)$', line)
            if item_match and not any(kw in line.lower() for kw in ['total', 'tax', 'subtotal', 'change', 'cash', 'card']):
                data['items'].append({
                    'name': item_match.group(1).strip(),
                    'price': float(item_match.group(2)),
                    'quantity': 1
                })
        
        # First line is often store name
        if lines and not data['store'].get('name'):
            data['store']['name'] = lines[0][:100]  # Limit length
        
        return data
    
    def _rate_limit(self):
        """Apply rate limiting to avoid API throttling."""
        min_interval = 0.5  # Minimum 500ms between requests
        elapsed = time.time() - self._last_request_time
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self._last_request_time = time.time()
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models for receipt extraction.
        
        Returns:
            List of model information dictionaries
        """
        return RECEIPT_EXTRACTION_MODELS.copy()
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model.
        
        Args:
            model_id: HuggingFace model ID
            
        Returns:
            ModelInfo or None if not found
        """
        try:
            api = HfApi(token=self.api_key)
            model_info = api.model_info(model_id)
            
            return ModelInfo(
                model_id=model_id,
                name=model_info.modelId.split('/')[-1],
                description=model_info.description or '',
                task=model_info.pipeline_tag or 'unknown',
                downloads=model_info.downloads or 0,
                likes=model_info.likes or 0,
                is_gated=model_info.gated or False,
                requires_token=model_info.gated or False,
                tags=list(model_info.tags) if model_info.tags else []
            )
            
        except Exception as e:
            logger.error(f"Failed to get model info for {model_id}: {e}")
            return None
    
    def search_models(
        self,
        query: str = "receipt",
        task: str = "document-question-answering",
        limit: int = 20
    ) -> List[ModelInfo]:
        """
        Search for models on HuggingFace Hub.
        
        Args:
            query: Search query
            task: Filter by task type
            limit: Maximum results to return
            
        Returns:
            List of ModelInfo objects
        """
        try:
            api = HfApi(token=self.api_key)
            models = api.list_models(
                search=query,
                task=task,
                sort="downloads",
                direction=-1,
                limit=limit
            )
            
            results = []
            for model in models:
                results.append(ModelInfo(
                    model_id=model.modelId,
                    name=model.modelId.split('/')[-1],
                    description='',
                    task=model.pipeline_tag or 'unknown',
                    downloads=model.downloads or 0,
                    likes=model.likes or 0,
                    is_gated=model.gated or False,
                    requires_token=model.gated or False,
                    tags=list(model.tags) if model.tags else []
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Model search failed: {e}")
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this session."""
        return {
            'requests': self._request_count,
            'api_key_configured': bool(self.api_key)
        }


def get_hf_inference() -> Optional[HuggingFaceInference]:
    """
    Get a configured HuggingFace Inference client.
    
    Returns:
        HuggingFaceInference instance or None if not available
    """
    if not HF_AVAILABLE:
        logger.warning("HuggingFace Hub not available")
        return None
    
    try:
        return HuggingFaceInference()
    except Exception as e:
        logger.error(f"Failed to create HuggingFace client: {e}")
        return None
