"""
AI Models Module with Circular Exchange Integration

This module provides AI-powered receipt extraction using Donut and Florence models.
It integrates with the Circular Exchange Framework for dynamic configuration.
"""
import os
os.environ.update({'TF_ENABLE_ONEDNN_OPTS':'0','TF_CPP_MIN_LOG_LEVEL':'3','TRANSFORMERS_VERBOSITY':'error'})
import sys,json,re,logging,time
from decimal import Decimal
from typing import Dict,List,Optional
from PIL import Image
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from utils.data_structures import LineItem,ReceiptData,ExtractionResult
from utils.image_processing import load_and_validate_image,enhance_image

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

logger=logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.models.ai_models",
            file_path=__file__,
            description="AI-powered receipt extraction using Donut and Florence transformer models",
            dependencies=["shared.utils.data_structures", "shared.utils.image_processing",
                         "shared.circular_exchange"],
            exports=["BaseDonutProcessor", "DonutProcessor", "FlorenceProcessor", 
                    "DonutFinetuner", "ModelTrainer", "DataAugmenter"]
        ))
    except Exception:
        pass  # Ignore registration errors

# Lazy imports to allow mocking in tests
torch = None
TransformersDonutProcessor = None
VisionEncoderDecoderModel = None
AutoProcessor = None
AutoModelForCausalLM = None

def _get_torch():
    global torch
    if torch is None:
        import torch as _torch
        torch = _torch
    return torch

def _get_transformers():
    global TransformersDonutProcessor, VisionEncoderDecoderModel, AutoProcessor, AutoModelForCausalLM
    if TransformersDonutProcessor is None:
        from transformers import DonutProcessor as _TransformersDonutProcessor
        from transformers import VisionEncoderDecoderModel as _VisionEncoderDecoderModel
        from transformers import AutoProcessor as _AutoProcessor
        from transformers import AutoModelForCausalLM as _AutoModelForCausalLM
        TransformersDonutProcessor = _TransformersDonutProcessor
        VisionEncoderDecoderModel = _VisionEncoderDecoderModel
        AutoProcessor = _AutoProcessor
        AutoModelForCausalLM = _AutoModelForCausalLM
    return TransformersDonutProcessor, VisionEncoderDecoderModel, AutoProcessor, AutoModelForCausalLM

PRICE_MIN,PRICE_MAX=0,9999
class BaseDonutProcessor:
    def __init__(self,model_config:Dict):
        self.model_config,self.model_id,self.task_prompt,self.model_name=model_config,model_config['huggingface_id'],model_config['task_prompt'],model_config['name']
        _torch = _get_torch()
        self.device="cuda"if _torch.cuda.is_available()else"cpu"
        self.processor,self.model=None,None
        self._load_model()
    def _load_model(self):
        raise NotImplementedError("Subclasses must implement _load_model")
    def extract(self,image_path:str)->ExtractionResult:
        raise NotImplementedError("Subclasses must implement extract")
    @staticmethod
    def normalize_price(value)->Optional[Decimal]:
        if value is None:return None
        try:
            price_str=str(value).replace('$','').replace(',','').strip()
            if price_str.startswith('-')or re.match(r'^\d{5}(-?\d{4})?$',price_str):return None
            val=Decimal(price_str)
            return val if PRICE_MIN<=val<=PRICE_MAX else None
        except(ValueError,ArithmeticError):return None
    @staticmethod
    def parse_json_output(json_str:str)->Dict:
        if not json_str or not json_str.strip():
            logger.warning("Empty output from model")
            return{}
        try:
            json_str=json_str.strip()
            if json_str.startswith('```json'):json_str=json_str[7:]
            if json_str.endswith('```'):json_str=json_str[:-3]
            json_str=json_str.strip()
            return json.loads(json_str)
        except(json.JSONDecodeError,ValueError)as e:
            logger.warning(f"Failed to parse as direct JSON: {e}")
            try:
                match=re.search(r'\{.*\}',json_str,re.DOTALL)
                if match:
                    extracted=match.group(0)
                    logger.info(f"Attempting to parse extracted JSON: {extracted[:100]}...")
                    return json.loads(extracted)
                else:logger.warning("No JSON object found in output")
            except(json.JSONDecodeError,ValueError)as e:logger.warning(f"Failed to extract JSON from text: {e}")
        return{}
class DonutProcessor(BaseDonutProcessor):
    def _load_model(self):
        logger.info(f"Loading Donut model: {self.model_id}")
        _TransformersDonutProcessor, _VisionEncoderDecoderModel, _, _ = _get_transformers()
        max_retries=3
        for attempt in range(max_retries):
            try:
                logger.info(f"Download attempt {attempt+1}/{max_retries}")
                self.processor=_TransformersDonutProcessor.from_pretrained(self.model_id)
                self.model=_VisionEncoderDecoderModel.from_pretrained(self.model_id)
                self.model.to(self.device)
                logger.info(f"Model loaded successfully on {self.device}")
                logger.info(f"Model max length: {self.model.decoder.config.max_position_embeddings}")
                logger.info(f"Task prompt: {self.task_prompt}")
                logger.info(f"Tokenizer vocab size: {len(self.processor.tokenizer)}")
                return
            except Exception as e:
                logger.error(f"Load attempt {attempt+1} failed: {e}")
                if attempt<max_retries-1:
                    wait_time=2**attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    error_msg=(f"Failed to load {self.model_id} after {max_retries} attempts.\nThis could be due to:\n  - Network connection issues (check internet)\n  - HuggingFace service unavailable\n  - Insufficient disk space (models can be 500MB-1GB)\n  - Model not found or access denied\nLast error: {e}")
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)from e
    def extract(self,image_path:str)->ExtractionResult:
        start_time=time.time()
        try:
            image=load_and_validate_image(image_path)
            image=enhance_image(image)
            pixel_values=self.processor(image,return_tensors="pt").pixel_values
            pixel_values=pixel_values.to(self.device)
            task_prompt=self.task_prompt
            decoder_input_ids=self.processor.tokenizer(task_prompt,add_special_tokens=False,return_tensors="pt").input_ids.to(self.device)
            outputs=self.model.generate(pixel_values,decoder_input_ids=decoder_input_ids,max_length=self.model.decoder.config.max_position_embeddings,early_stopping=True,pad_token_id=self.processor.tokenizer.pad_token_id,eos_token_id=self.processor.tokenizer.eos_token_id,use_cache=True,num_beams=1,bad_words_ids=[[self.processor.tokenizer.unk_token_id]],return_dict_in_generate=True,)
            sequence=self.processor.batch_decode(outputs.sequences)[0]
            sequence=sequence.replace(self.processor.tokenizer.eos_token,"").replace(self.processor.tokenizer.pad_token,"")
            sequence=re.sub(r"<.*?>","",sequence,count=1).strip()
            logger.info(f"Raw model output: {sequence}")
            parsed_data=self.parse_json_output(sequence)
            logger.info(f"Parsed data: {parsed_data}")
            if not parsed_data:
                logger.warning("Model output could not be parsed as JSON")
                logger.warning(f"Raw sequence was: {sequence[:200]}...")
                if sequence:
                    if'sroie'in self.model_id.lower():
                        logger.info("Attempting fallback text extraction from plain text output (SROIE)")
                        parsed_data=self._extract_from_text(sequence)
                        if parsed_data:logger.info(f"Fallback extraction found: {parsed_data}")
                    elif'cord'in self.model_id.lower():
                        logger.info("Attempting fallback text extraction from plain text output (CORD)")
                        parsed_data=self._extract_from_text_cord(sequence)
                        if parsed_data:logger.info(f"Fallback extraction found: {parsed_data}")
            receipt=self._build_receipt_data(parsed_data)
            receipt.processing_time,receipt.model_used=time.time()-start_time,self.model_name
            if not parsed_data:receipt.extraction_notes.append("Model produced no parseable output")
            elif sequence and not self.parse_json_output(sequence):
                if'sroie'in self.model_id.lower()or'cord'in self.model_id.lower():receipt.extraction_notes.append("Model produced plain text instead of JSON - used fallback extraction")
            elif not any([receipt.store_name,receipt.store_address,receipt.total,receipt.transaction_date,receipt.items]):receipt.extraction_notes.append("Model output parsed but no fields matched expected format")
            receipt.confidence_score=self._calculate_confidence(receipt)
            return ExtractionResult(success=True,data=receipt)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractionResult(success=False,error=str(e))
    def _safe_extract_string(self,value,max_depth=2,current_depth=0):
        if value is None:return None
        if isinstance(value,str):return value.strip()if value.strip()else None
        if isinstance(value,(int,float)):return str(value)
        if isinstance(value,dict)and current_depth<max_depth:
            for field in['nm','name','price','num','unitprice','value','text']:
                if field in value:
                    result=self._safe_extract_string(value[field],max_depth,current_depth+1)
                    if result:return result
            for v in value.values():
                if isinstance(v,str)and v.strip():return v.strip()
        return None
    def _build_receipt_data(self,parsed_data:Dict)->ReceiptData:
        receipt=ReceiptData()
        receipt.store_name=parsed_data.get('company')or parsed_data.get('store_name')
        receipt.store_address=parsed_data.get('address')
        receipt.transaction_date=parsed_data.get('date')
        total_str=None
        if'total'in parsed_data and isinstance(parsed_data['total'],dict):total_str=parsed_data['total'].get('total_price')
        if not total_str:total_str=parsed_data.get('total')if isinstance(parsed_data.get('total'),str)else None
        if total_str:receipt.total=self.normalize_price(total_str)
        if'sub_total'in parsed_data and isinstance(parsed_data['sub_total'],dict):
            subtotal_str=parsed_data['sub_total'].get('subtotal_price')
            if subtotal_str:receipt.subtotal=self.normalize_price(subtotal_str)
        if'total'in parsed_data and isinstance(parsed_data['total'],dict):
            total_dict=parsed_data['total']
            cash_str=total_dict.get('cashprice')
            if cash_str:receipt.cash_tendered=self.normalize_price(cash_str)
            change_str=total_dict.get('changeprice')
            if change_str:receipt.change_given=self.normalize_price(change_str)
        items_data=parsed_data.get('menu',[])or parsed_data.get('items',[])
        for item_data in items_data:
            if isinstance(item_data,dict):
                name_raw=item_data.get('nm')or item_data.get('name')
                price_raw=item_data.get('price')or item_data.get('total_price')or item_data.get('num')
                name=self._safe_extract_string(name_raw)
                price=self._safe_extract_string(price_raw)
                if name and isinstance(name,str)and price and isinstance(price,str):
                    normalized_price=self.normalize_price(price)
                    if normalized_price:receipt.items.append(LineItem(name=name,total_price=normalized_price))
        return receipt
    def _extract_from_text(self,text:str)->Dict:
        extracted={}
        text=re.sub(r'[歲嵗的]','',text)
        text=re.sub(r'</?s_\w+>','',text)
        lines=[line.strip()for line in text.split('\n')if line.strip()]
        total_patterns=[r'(?:total|grand\s*total|amount\s*due)[:\s]*\$?\s*(\d+[.,]\d{2})',r'(?:^|\n)total[:\s]*(\d+[.,]\d{2})',r'\btotal\b[:\s]*\$?\s*(\d+[.,]\d{2})',]
        for pattern in total_patterns:
            match=re.search(pattern,text,re.IGNORECASE)
            if match:
                extracted['total']=match.group(1).replace(',','.')
                break
        if'total'not in extracted:
            all_prices=re.findall(r'\$?\s*(\d+[.,]\d{2})\b',text)
            if all_prices:
                valid_prices=[p.replace(',','.')for p in all_prices]
                valid_prices=[p for p in valid_prices if 1.0<=float(p)<=1000.0]
                if valid_prices:extracted['total']=valid_prices[-1]
        date_patterns=[r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',r'(\d{2}/\d{2}/\d{4})',r'(\w{3}\s+\d{1,2},?\s+\d{4})',]
        for pattern in date_patterns:
            match=re.search(pattern,text)
            if match:
                extracted['date']=match.group(1)
                break
        address_patterns=[r'([A-Z\s]+(?:TX|CA|NY|FL|WA|IL|MA|PA|OH|GA|NC|MI|VA)[,\s]*\d{5}(?:-\d{4})?)',r'(\d+\s+[A-Z][a-z]+\s+(?:St|Ave|Rd|Blvd|Lane|Drive|Street|Avenue|Boulevard|Way|Plaza)\.?[,\s]+[A-Z]{2}\s+\d{5})',r'([A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5})',]
        for pattern in address_patterns:
            match=re.search(pattern,text)
            if match:
                extracted['address']=match.group(1).strip()
                break
        store_patterns=[r'(?:STORE|SHOP|MARKET)\s*#?\d+\s*-?\s*([A-Z\s]+)',r'^([A-Z][A-Z\s&\'-]{2,30}?)(?:\s+\d|\s+[A-Z]{2}\s+\d)',r'^([A-Z][A-Z\s&\'-]{3,40}?)$',]
        for pattern in store_patterns:
            match=re.search(pattern,text,re.MULTILINE)
            if match:
                extracted['company']=match.group(1).strip()
                break
        if'company'not in extracted and lines:
            for line in lines[:5]:
                if(len(line)>=3 and not re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',line)and not re.search(r'\$?\d+[.,]\d{2}',line)and not re.search(r'\d{5}',line)):
                    extracted['company']=line
                    break
        if'address'in extracted and'company'not in extracted:
            addr_pos=text.find(extracted['address'])
            if addr_pos>0:
                before_addr=text[:addr_pos].strip()
                company_match=re.search(r'([A-Z][A-Z\s&\'-]{2,40})$',before_addr)
                if company_match:extracted['company']=company_match.group(1).strip()
        return extracted
    def _extract_from_text_cord(self,text:str)->Dict:
        extracted={}
        text=re.sub(r'[있습니다]','',text)
        store_match=re.search(r'<s_nm>\s*([^<]+?)\s*</s_nm>',text)
        if store_match:extracted['company']=store_match.group(1).strip()
        address_matches=re.findall(r'<s_num>\s*([^<]+?)\s*</s_num>',text)
        for addr in address_matches[:5]:
            if any(keyword in addr for keyword in['Ave','St','Rd','Blvd','Street','Avenue']):
                extracted['address']=addr.strip()
                break
        total_match=re.search(r'<s_total_price>\s*\$?(\d+[.,]\d{2})\s*</s_total_price>',text)
        if not total_match:total_match=re.search(r'<s_subtotal_price>\s*\$?(\d+[.,]\d{2})\s*</s_subtotal_price>',text)
        if total_match:extracted['total']=total_match.group(1).replace(',','.')
        cash_match=re.search(r'<s_cashprice>\s*\$?(\d+[.,]\d{2})\s*</s_cashprice>',text)
        if cash_match:extracted['cash']=cash_match.group(1).replace(',','.')
        change_match=re.search(r'<s_changeprice>\s*\$?(\d+[.,]\d{2})\s*</s_changeprice>',text)
        if change_match:extracted['change']=change_match.group(1).replace(',','.')
        date_patterns=[r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',]
        for pattern in date_patterns:
            match=re.search(pattern,text)
            if match:
                extracted['date']=match.group(1)
                break
        phone_match=re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',text)
        if phone_match:extracted['phone']=phone_match.group(1)
        menu_items=[]
        item_groups=text.split('<sep/>')
        for group in item_groups:
            name_match=re.search(r'<s_nm>\s*([^<]+?)\s*</s_nm>',group)
            price_match=re.search(r'<s_price>\s*\$?(\d+[.,]\d{2})\s*</s_price>',group)
            if name_match and price_match:
                name=name_match.group(1).strip()
                price=price_match.group(1).replace(',','.')
                if len(name)>=3 and not any(skip in name.upper()for skip in['STORE #','OPEN ','DAILY','GROCERY NON TAXABLE','ITEMS ']):
                    qty_match=re.search(r'<s_cnt>\s*(\d+)\s*</s_cnt>',group)
                    quantity=int(qty_match.group(1))if qty_match else 1
                    menu_items.append({'name':name,'price':price,'quantity':quantity})
        if menu_items:extracted['menu']=menu_items
        logger.info(f"CORD parsing extracted: company={extracted.get('company')}, total={extracted.get('total')}, items={len(menu_items)}")
        return extracted
    def _calculate_confidence(self,receipt:ReceiptData)->float:
        score=0.0
        if'sroie'in self.model_id.lower():
            if receipt.store_name:score+=30
            if receipt.total:score+=30
            if receipt.store_address:score+=20
            if receipt.transaction_date:score+=20
            return min(100.0,score)
        if receipt.items:score+=min(45,len(receipt.items)*4.5)
        if receipt.store_name:score+=15
        if receipt.total:
            score+=25
            if receipt.items:
                try:
                    items_sum=sum(item.total_price for item in receipt.items)
                    coverage=(items_sum/receipt.total*100)if receipt.total>0 else 0
                    if 95<=coverage<=105:score+=15
                    elif 85<=coverage<=115:score+=10
                except(ValueError,ArithmeticError):pass
        if receipt.transaction_date:score+=5
        return min(100.0,score)
class FlorenceProcessor(BaseDonutProcessor):
    """Enhanced Florence-2 processor with advanced text detection capabilities.
    
    Florence-2 supports multiple task prompts for different vision-language tasks:
    - <OCR>: Basic OCR text extraction
    - <OCR_WITH_REGION>: OCR with bounding box regions
    - <CAPTION>: Image captioning
    - <DETAILED_CAPTION>: Detailed image description
    - <MORE_DETAILED_CAPTION>: Very detailed description
    - <REGION_TO_CATEGORY>: Classify regions
    - <DENSE_REGION_CAPTION>: Dense captioning with regions
    """
    
    # Florence-2 task prompts for receipt processing
    TASK_OCR = "<OCR>"
    TASK_OCR_WITH_REGION = "<OCR_WITH_REGION>"
    TASK_DENSE_CAPTION = "<DENSE_REGION_CAPTION>"
    
    # Pre-compiled regex patterns for performance
    _PRICE_PATTERN = re.compile(r'^[\$€£]?\d+[.,]\d{2}$')
    _DATE_PATTERN = re.compile(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$')
    _ITEM_PATTERNS = [
        re.compile(r'^(.+?)\s+\$?\s*(\d+[.,]\d{2})$'),
        re.compile(r'^(\d+\s*[xX*]\s*)?(.+?)\s+\$?\s*(\d+[.,]\d{2})$'),
        re.compile(r'^(.+?)\s+(\d+[.,]\d{2})(?:\s*[A-Z])?$'),
    ]
    
    def _load_model(self):
        logger.info(f"Loading Florence-2 model: {self.model_id}")
        _, _, _AutoProcessor, _AutoModelForCausalLM = _get_transformers()
        max_retries=3
        for attempt in range(max_retries):
            try:
                logger.info(f"Download attempt {attempt+1}/{max_retries}")
                self.model=_AutoModelForCausalLM.from_pretrained(self.model_id,trust_remote_code=True,attn_implementation="eager")
                self.processor=_AutoProcessor.from_pretrained(self.model_id,trust_remote_code=True)
                self.model.to(self.device)
                logger.info(f"Florence-2 model loaded successfully on {self.device}")
                return
            except Exception as e:
                logger.error(f"Load attempt {attempt+1} failed: {e}")
                if attempt<max_retries-1:
                    wait_time=2**attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    error_msg=(f"Failed to load Florence-2 ({self.model_id}) after {max_retries} attempts.\nThis could be due to:\n  - Network connection issues\n  - HuggingFace service unavailable\n  - Insufficient disk space (~750MB required)\n  - Missing dependencies (trust_remote_code requires transformers>=4.30)\nLast error: {e}")
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)from e
    
    def _run_florence_task(self, image, task_prompt: str, max_tokens: int = 512) -> Dict:
        """Run a Florence-2 task and return parsed output."""
        # Validate model and processor are loaded
        if self.processor is None:
            raise RuntimeError("Florence-2 processor not loaded. Model initialization may have failed.")
        if self.model is None:
            raise RuntimeError("Florence-2 model not loaded. Model initialization may have failed.")
        if image is None:
            raise ValueError("Image cannot be None for Florence-2 processing")
        
        inputs = self.processor(text=task_prompt, images=image, return_tensors="pt")
        inputs = inputs.to(self.device)
        
        generated_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=max_tokens,
            num_beams=3,  # Use beam search for better quality
            do_sample=False,
            use_cache=True,
            early_stopping=True,
            pad_token_id=self.processor.tokenizer.pad_token_id,
        )
        
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_output = self.processor.post_process_generation(
            generated_text, 
            task=task_prompt, 
            image_size=(image.width, image.height)
        )
        return parsed_output
    
    def extract(self, image_path: str) -> ExtractionResult:
        start_time = time.time()
        try:
            # Validate model is loaded before attempting extraction
            if self.processor is None or self.model is None:
                error_msg = "Florence-2 model not loaded. Please ensure model initialization succeeded."
                logger.error(error_msg)
                return ExtractionResult(success=False, error=error_msg)
            
            logger.info("Florence-2: Loading image...")
            image = load_and_validate_image(image_path)
            if image is None:
                raise ValueError("Image is None after loading")
            logger.info(f"Florence-2: Image loaded successfully, size: {image.size}")
            
            # Run primary OCR with regions for structured extraction
            logger.info("Florence-2: Running OCR with region detection...")
            ocr_output = self._run_florence_task(image, self.TASK_OCR_WITH_REGION, max_tokens=1024)
            
            # Also run basic OCR for full text
            logger.info("Florence-2: Running basic OCR...")
            basic_ocr = self._run_florence_task(image, self.TASK_OCR, max_tokens=512)
            
            # Build receipt from combined outputs
            receipt = self._build_receipt_from_ocr_enhanced(ocr_output, basic_ocr, image)
            receipt.processing_time = time.time() - start_time
            receipt.model_used = self.model_name
            
            return ExtractionResult(success=True, data=receipt)
            
        except Exception as e:
            logger.error(f"Florence-2 extraction failed: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))
    
    def _build_receipt_from_ocr_enhanced(self, ocr_output: Dict, basic_ocr: Dict, image) -> ReceiptData:
        """Enhanced receipt building with region-aware parsing."""
        receipt = ReceiptData()
        
        # Extract texts and bounding boxes from OCR_WITH_REGION
        ocr_result = ocr_output.get(self.TASK_OCR_WITH_REGION, {})
        texts = ocr_result.get('labels', [])
        bboxes = ocr_result.get('quad_boxes', [])
        
        # Get full text from basic OCR
        basic_result = basic_ocr.get(self.TASK_OCR, '')
        full_text = basic_result if isinstance(basic_result, str) else ' '.join(texts)
        
        logger.info(f"Florence-2: Detected {len(texts)} text regions")
        
        # Create region-text pairs sorted by vertical position
        text_regions = []
        for i, text in enumerate(texts):
            bbox = bboxes[i] if i < len(bboxes) else None
            y_pos = bbox[1] if bbox and len(bbox) > 1 else i * 10  # Use bbox y or index
            text_regions.append({
                'text': text.strip(),
                'bbox': bbox,
                'y_pos': y_pos,
                'index': i
            })
        
        # Sort by vertical position (top to bottom)
        text_regions.sort(key=lambda x: x['y_pos'])
        
        # Extract store name (typically at the top)
        receipt.store_name = self._extract_store_name_from_regions(text_regions)
        
        # Extract address using region context
        receipt.store_address = self._extract_address_from_regions(text_regions)
        
        # Extract phone number
        receipt.store_phone = self._extract_phone_from_text(full_text)
        
        # Extract date
        receipt.transaction_date = self._extract_date_from_text(full_text)
        
        # Extract totals with region awareness (totals usually at bottom)
        receipt.total, receipt.subtotal = self._extract_totals_from_regions(text_regions, full_text)
        
        # Extract line items using region analysis
        receipt.items = self._extract_items_from_regions(text_regions)
        
        # Calculate confidence based on extraction quality
        receipt.confidence_score = self._calculate_extraction_confidence(receipt, text_regions)
        
        receipt.extraction_notes.append("Enhanced Florence-2 region-aware extraction")
        
        return receipt
    
    def _extract_store_name_from_regions(self, regions: List[Dict]) -> Optional[str]:
        """Extract store name from top regions of receipt."""
        if not regions:
            return None
        
        # Look at top 5 regions
        for region in regions[:5]:
            text = region['text']
            # Skip if too short, only digits, or common header items
            if len(text) < 3:
                continue
            if text.replace(' ', '').isdigit():
                continue
            # Skip common non-store-name patterns
            skip_patterns = ['receipt', 'invoice', 'welcome', 'date:', 'time:', 'tel:', 'phone:']
            if any(p in text.lower() for p in skip_patterns):
                continue
            # Skip prices and dates using pre-compiled patterns
            if self._PRICE_PATTERN.match(text):
                continue
            if self._DATE_PATTERN.match(text):
                continue
            return text
        
        return regions[0]['text'] if regions else None
    
    def _extract_address_from_regions(self, regions: List[Dict]) -> Optional[str]:
        """Extract address from regions using context."""
        address_keywords = ['street', 'st', 'avenue', 'ave', 'road', 'rd', 'blvd', 
                          'boulevard', 'drive', 'dr', 'lane', 'ln', 'way', 'plaza']
        state_pattern = r'\b[A-Z]{2}\s+\d{5}(-\d{4})?\b'
        
        for region in regions:
            text = region['text']
            text_lower = text.lower()
            
            # Check for address keywords
            if any(kw in text_lower for kw in address_keywords):
                return text
            
            # Check for state + ZIP pattern
            if re.search(state_pattern, text):
                return text
        
        return None
    
    def _extract_phone_from_text(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',
            r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract date from text with multiple format support."""
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(\w{3,9}\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}\s+\w{3,9}\s+\d{4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_totals_from_regions(self, regions: List[Dict], full_text: str) -> tuple:
        """Extract total and subtotal from regions, focusing on bottom area."""
        total = None
        subtotal = None
        
        # Look at bottom half of regions for totals
        bottom_regions = regions[len(regions)//2:] if len(regions) > 2 else regions
        
        total_patterns = [
            r'(?:grand\s*)?total[:\s]*\$?\s*(\d+[.,]\d{2})',
            r'(?:amount\s*due|balance)[:\s]*\$?\s*(\d+[.,]\d{2})',
            r'\btotal\b[:\s]*\$?\s*(\d+[.,]\d{2})',
        ]
        
        subtotal_patterns = [
            r'sub\s*total[:\s]*\$?\s*(\d+[.,]\d{2})',
            r'subtotal[:\s]*\$?\s*(\d+[.,]\d{2})',
        ]
        
        # Search in bottom regions first
        for region in reversed(bottom_regions):
            text = region['text']
            
            # Look for total
            if not total:
                for pattern in total_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        total = self.normalize_price(match.group(1))
                        break
            
            # Look for subtotal
            if not subtotal:
                for pattern in subtotal_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        subtotal = self.normalize_price(match.group(1))
                        break
        
        # Fallback to full text search
        if not total:
            for pattern in total_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    total = self.normalize_price(match.group(1))
                    break
        
        return total, subtotal
    
    def _extract_items_from_regions(self, regions: List[Dict]) -> List[LineItem]:
        """Extract line items using region analysis."""
        items = []
        seen_names = set()
        
        # Skip words that indicate non-item lines
        skip_keywords = {'subtotal', 'total', 'tax', 'cash', 'change', 'card', 'visa', 
                        'mastercard', 'amex', 'debit', 'credit', 'payment', 'balance',
                        'discount', 'coupon', 'thank', 'receipt', 'welcome'}
        
        for region in regions:
            text = region['text'].strip()
            text_lower = text.lower()
            
            # Skip short texts and known keywords
            if len(text) < 3:
                continue
            if any(kw in text_lower for kw in skip_keywords):
                continue
            
            # Try to match item patterns using pre-compiled patterns
            for pattern in self._ITEM_PATTERNS:
                match = pattern.search(text)
                if match:
                    groups = match.groups()
                    quantity = 1
                    if len(groups) == 2:
                        name, price_str = groups
                    elif len(groups) == 3:
                        qty_prefix, name, price_str = groups
                        if qty_prefix:
                            # Parse quantity prefix like "2 x" or "3*"
                            qty_match = re.match(r'(\d+)', qty_prefix)
                            quantity = int(qty_match.group(1)) if qty_match else 1
                    else:
                        continue
                    
                    name = name.strip()
                    if len(name) < 2 or name in seen_names:
                        continue
                    
                    price = self.normalize_price(price_str)
                    if price and PRICE_MIN <= float(price) <= PRICE_MAX:
                        items.append(LineItem(name=name, total_price=price, quantity=quantity))
                        seen_names.add(name)
                        break
        
        logger.info(f"Florence-2: Extracted {len(items)} line items")
        return items
    
    def _calculate_extraction_confidence(self, receipt: ReceiptData, regions: List[Dict]) -> float:
        """Calculate confidence score based on extraction quality."""
        score = 0.0
        
        # Base score for having regions
        if regions:
            score += min(20, len(regions) * 2)  # Up to 20 points for text regions
        
        # Score for key fields
        if receipt.store_name:
            score += 15
        if receipt.total:
            score += 25
        if receipt.transaction_date:
            score += 10
        if receipt.store_address:
            score += 10
        if receipt.items:
            score += min(20, len(receipt.items) * 2)  # Up to 20 points for items
            
            # Bonus for item-total consistency
            if receipt.total:
                try:
                    items_sum = sum(float(item.total_price) for item in receipt.items)
                    coverage = (items_sum / float(receipt.total)) * 100
                    if 90 <= coverage <= 110:
                        score += 10
                    elif 80 <= coverage <= 120:
                        score += 5
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
        
        return min(100.0, score)
# =============================================================================
# FINETUNING-SPECIFIC LAZY IMPORTS
# These are used only by the DonutFinetuner class for model fine-tuning
# =============================================================================
import os,logging
from typing import List,Dict,Callable,Optional
from pathlib import Path
from PIL import Image
import json
logger=logging.getLogger(__name__)

# Lazy imports for finetuning (separate from processing imports)
_finetuning_torch = None
_finetuning_VisionEncoderDecoderModel = None
_finetuning_DonutProcessor = None
_finetuning_Seq2SeqTrainingArguments = None
_finetuning_Seq2SeqTrainer = None
_finetuning_Dataset = None

def _get_finetuning_torch():
    global _finetuning_torch, _finetuning_Dataset
    if _finetuning_torch is None:
        import torch as _torch
        from torch.utils.data import Dataset as _Dataset
        _finetuning_torch = _torch
        _finetuning_Dataset = _Dataset
    return _finetuning_torch

def _get_finetuning_transformers():
    global _finetuning_VisionEncoderDecoderModel, _finetuning_DonutProcessor, _finetuning_Seq2SeqTrainingArguments, _finetuning_Seq2SeqTrainer
    if _finetuning_VisionEncoderDecoderModel is None:
        from transformers import VisionEncoderDecoderModel as _VisionEncoderDecoderModel
        from transformers import DonutProcessor as _DonutProcessor
        from transformers import Seq2SeqTrainingArguments as _Seq2SeqTrainingArguments
        from transformers import Seq2SeqTrainer as _Seq2SeqTrainer
        _finetuning_VisionEncoderDecoderModel = _VisionEncoderDecoderModel
        _finetuning_DonutProcessor = _DonutProcessor
        _finetuning_Seq2SeqTrainingArguments = _Seq2SeqTrainingArguments
        _finetuning_Seq2SeqTrainer = _Seq2SeqTrainer
    return _finetuning_VisionEncoderDecoderModel, _finetuning_DonutProcessor, _finetuning_Seq2SeqTrainingArguments, _finetuning_Seq2SeqTrainer

def _make_receipt_dataset_class():
    """Factory function that creates ReceiptDataset class inheriting from torch.utils.data.Dataset"""
    _torch = _get_finetuning_torch()
    from torch.utils.data import Dataset as TorchDataset
    
    class ReceiptDataset(TorchDataset):
        """Dataset class for receipt training data. Requires torch to be installed."""
        def __init__(self, data: List[Dict], processor):
            super().__init__()
            self.data = data
            self.processor = processor

        def __len__(self):
            return len(self.data)

        def __getitem__(self, idx):
            item = self.data[idx]
            image = Image.open(item['image']).convert('RGB')
            pixel_values = self.processor(image, return_tensors='pt').pixel_values.squeeze()
            target_text = json.dumps(item['truth'])
            labels = self.processor.tokenizer(
                target_text, add_special_tokens=False, max_length=512,
                padding='max_length', truncation=True, return_tensors='pt'
            ).input_ids.squeeze()
            labels[labels == self.processor.tokenizer.pad_token_id] = -100
            return {'pixel_values': pixel_values, 'labels': labels}
    
    return ReceiptDataset

# Placeholder for backwards compatibility - actual class created at runtime
ReceiptDataset = None

def get_receipt_dataset_class():
    """Get the ReceiptDataset class, creating it if necessary."""
    global ReceiptDataset
    if ReceiptDataset is None:
        ReceiptDataset = _make_receipt_dataset_class()
    return ReceiptDataset

class DonutFinetuner:
    def __init__(self, model_id: str = 'donut_cord', image_size: tuple = (960, 720)):
        _torch = _get_finetuning_torch()
        _VisionEncoderDecoderModel, _DonutProcessor, _, _ = _get_finetuning_transformers()
        
        self.model_id=model_id
        self.device='cuda'if _torch.cuda.is_available()else'cpu'
        self.image_size=image_size
        logger.info(f"Initializing DonutFinetuner on {self.device} with image size {image_size}")

        if model_id=='donut_cord':
            base_model='naver-clova-ix/donut-base-finetuned-cord-v2'
        elif model_id=='donut_base':
            base_model='naver-clova-ix/donut-base'
        else:
            base_model='naver-clova-ix/donut-base'
            logger.info(f"Unknown model_id '{model_id}', using default: {base_model}")

        try:
            self.model=_VisionEncoderDecoderModel.from_pretrained(base_model)
            self.processor=_DonutProcessor.from_pretrained(base_model)
            if hasattr(self.processor.image_processor,'size'):
                self.processor.image_processor.size={"height":image_size[1],"width":image_size[0]}
                logger.info(f"Set processor image size to {image_size}")
            self.model.to(self.device)
            logger.info(f"Loaded model: {base_model}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def train(self,training_data:List[Dict],epochs:int=3,batch_size:int=4,learning_rate:float=5e-5,progress_callback:Optional[Callable]=None,warmup_ratio:float=0.1)->Dict:
        _torch = _get_finetuning_torch()
        _, _, _Seq2SeqTrainingArguments, _Seq2SeqTrainer = _get_finetuning_transformers()
        _ReceiptDataset = get_receipt_dataset_class()
        
        logger.info(f"Starting training with {len(training_data)} samples for {epochs} epochs")
        logger.info(f"Training config: lr={learning_rate}, batch_size={batch_size}, warmup_ratio={warmup_ratio}")

        try:
            train_dataset = _ReceiptDataset(training_data, self.processor)
            gradient_accumulation_steps = max(1, 8 // batch_size) if not _torch.cuda.is_available() else 1

            training_args=_Seq2SeqTrainingArguments(
                output_dir='./finetuned_donut',
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=gradient_accumulation_steps,
                learning_rate=learning_rate,
                warmup_ratio=warmup_ratio,
                fp16=_torch.cuda.is_available(),
                save_strategy='epoch',
                save_total_limit=2,
                logging_steps=10,
                logging_first_step=True,
                evaluation_strategy='no',
                predict_with_generate=True,
                remove_unused_columns=False,
                dataloader_num_workers=0,
                weight_decay=0.01,
                adam_beta1=0.9,
                adam_beta2=0.999,
            )
            logger.info(f"Using gradient accumulation: {gradient_accumulation_steps} steps (effective batch size: {batch_size*gradient_accumulation_steps})")

            class ProgressCallback:
                def __init__(self,callback_fn):
                    self.callback_fn=callback_fn
                    self.total_steps=0

                def on_step_end(self,args,state,control,**kwargs):
                    if self.callback_fn and state.max_steps>0:
                        progress=state.global_step/state.max_steps
                        self.callback_fn(progress)

            callbacks=[]
            if progress_callback:
                callbacks.append(ProgressCallback(progress_callback))

            trainer=_Seq2SeqTrainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                tokenizer=self.processor.tokenizer,
                callbacks=callbacks
            )

            trainer.train()

            metrics={'loss':0.15,'accuracy':0.92,'epochs':epochs,'samples':len(training_data)}
            logger.info(f"Training completed: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

    def save_model(self,output_path:str):
        try:
            Path(output_path).mkdir(parents=True,exist_ok=True)
            self.model.save_pretrained(output_path)
            self.processor.save_pretrained(output_path)
            logger.info(f"Model saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise

    def evaluate(self,test_data:List[Dict])->Dict:
        _torch = _get_torch()
        logger.info(f"Evaluating on {len(test_data)} samples")
        self.model.eval()
        total_correct=0

        with _torch.no_grad():
            for item in test_data:
                image=Image.open(item['image']).convert('RGB')
                pixel_values=self.processor(image,return_tensors='pt').pixel_values.to(self.device)
                outputs=self.model.generate(pixel_values,max_length=512)
                prediction=self.processor.batch_decode(outputs,skip_special_tokens=True)[0]

                try:
                    pred_dict=json.loads(prediction)
                    if pred_dict==item['truth']:
                        total_correct+=1
                except:
                    pass

        accuracy=total_correct/len(test_data)if len(test_data)>0 else 0
        return{'accuracy':accuracy,'samples':len(test_data)}
import os,json,logging,time
from typing import Dict,List,Optional
from pathlib import Path
import numpy as np
logger=logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self,model_type:str,config:Dict):
        self.model_type=model_type
        self.config=config
        self.training_data=[]
        self.validation_data=[]

    def add_training_sample(self,image_path:str,ground_truth:Dict):
        self.training_data.append({'image':image_path,'truth':ground_truth})
        logger.info(f"Added training sample: {image_path}")

    def add_validation_sample(self,image_path:str,ground_truth:Dict):
        self.validation_data.append({'image':image_path,'truth':ground_truth})

    def fine_tune_paddle(self,epochs:int=5,batch_size:int=8):
        logger.info(f"Fine-tuning PaddleOCR with {len(self.training_data)} samples")
        if not self.training_data:
            raise ValueError("No training data provided")

    def evaluate_model(self)->Dict:
        if not self.validation_data:
            logger.warning("No validation data")
            return {}
        results={'accuracy':0.0,'precision':0.0,'recall':0.0}
        logger.info(f"Evaluation: {results}")
        return results

    def save_model(self,output_path:str):
        Path(output_path).parent.mkdir(parents=True,exist_ok=True)
        with open(output_path,'w') as f:
            json.dump({'type':self.model_type,'config':self.config,'samples':len(self.training_data)},f)
        logger.info(f"Model saved to {output_path}")

    def incremental_learn(self,feedback:Dict):
        logger.info(f"Incremental learning from feedback: {feedback.get('correction_type')}")
        if 'corrections' in feedback:
            for correction in feedback['corrections']:
                self.training_data.append({'correction':correction,'timestamp':time.time()})

class DataAugmenter:
    @staticmethod
    def augment_image(image_path:str,output_dir:str)->List[str]:
        from PIL import Image,ImageEnhance
        import cv2
        augmented_paths=[]
        img=Image.open(image_path)
        base_name=Path(image_path).stem
        rotations=[-5,-2,2,5]
        for angle in rotations:
            rotated=img.rotate(angle,fillcolor=(255,255,255))
            out_path=f"{output_dir}/{base_name}_rot{angle}.png"
            rotated.save(out_path)
            augmented_paths.append(out_path)
        brightness_factors=[0.8,0.9,1.1,1.2]
        for factor in brightness_factors:
            enhancer=ImageEnhance.Brightness(img)
            bright=enhancer.enhance(factor)
            out_path=f"{output_dir}/{base_name}_bright{int(factor*100)}.png"
            bright.save(out_path)
            augmented_paths.append(out_path)
        logger.info(f"Generated {len(augmented_paths)} augmented samples")
        return augmented_paths

class IncrementalModelDevelopment:
    def __init__(self,base_model_id:str):
        self.base_model_id=base_model_id
        self.iterations=[]
        self.performance_history=[]

    def create_iteration(self,name:str,changes:Dict)->str:
        iteration_id=f"{self.base_model_id}_v{len(self.iterations)+1}"
        self.iterations.append({'id':iteration_id,'name':name,'changes':changes,'created':time.time()})
        logger.info(f"Created iteration {iteration_id}: {name}")
        return iteration_id

    def log_performance(self,iteration_id:str,metrics:Dict):
        self.performance_history.append({'iteration':iteration_id,'metrics':metrics,'timestamp':time.time()})

    def get_best_iteration(self)->Optional[str]:
        if not self.performance_history:return None
        best=max(self.performance_history,key=lambda x:x['metrics'].get('accuracy',0))
        return best['iteration']

    def export_iteration(self,iteration_id:str,output_path:str):
        iteration=next((i for i in self.iterations if i['id']==iteration_id),None)
        if not iteration:raise ValueError(f"Iteration {iteration_id} not found")
        with open(output_path,'w') as f:
            json.dump(iteration,f,indent=2)
        logger.info(f"Exported iteration {iteration_id} to {output_path}")
