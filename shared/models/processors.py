import logging,time
from typing import Dict,Optional
from abc import ABC,abstractmethod
logger=logging.getLogger(__name__)
class ProcessorInitializationError(Exception):
    pass
class ProcessorHealthCheckError(Exception):
    pass
class BaseProcessor(ABC):
    def __init__(self,model_config:Dict):
        self.model_config,self.model_name,self.model_id=model_config,model_config.get('name','unknown'),model_config.get('id','unknown')
        self.initialized,self.initialization_error,self.last_health_check=False,None,None
    @abstractmethod
    def _load_model(self):
        pass
    @abstractmethod
    def _health_check(self)->bool:
        pass
    @abstractmethod
    def extract(self,image_path:str)->'ExtractionResult':
        pass
    def initialize(self,retry_count:int=2):
        for attempt in range(retry_count+1):
            try:
                logger.info(f"Initializing {self.model_name} (attempt {attempt+1}/{retry_count+1})")
                self._load_model()
                if not self._health_check():raise ProcessorInitializationError(f"{self.model_name} loaded but failed health check")
                self.initialized,self.initialization_error=True,None
                logger.info(f"{self.model_name} initialized successfully")
                return
            except Exception as e:
                logger.error(f"Initialization attempt {attempt+1} failed: {e}")
                self.initialization_error=str(e)
                if attempt<retry_count:
                    wait_time=2**attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    error_msg=(f"Failed to initialize {self.model_name} after {retry_count+1} attempts. Last error: {e}")
                    raise ProcessorInitializationError(error_msg)from e
    def ensure_healthy(self):
        if not self.initialized:raise ProcessorHealthCheckError(f"{self.model_name} is not initialized. Initialization error: {self.initialization_error}")
        if not self._health_check():raise ProcessorHealthCheckError(f"{self.model_name} health check failed")
        self.last_health_check=time.time()
    def get_status(self)->Dict:
        return{'model_name':self.model_name,'model_id':self.model_id,'initialized':self.initialized,'initialization_error':self.initialization_error,'last_health_check':self.last_health_check,'healthy':self._health_check()if self.initialized else False}
import os,sys,re,logging,time
from decimal import Decimal
from typing import Dict,List,Optional
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from utils.data_structures import LineItem,ReceiptData,ExtractionResult
from .ocr_common import (
    SKIP_KEYWORDS, PRICE_MIN, PRICE_MAX, normalize_price,
    extract_date, extract_total, extract_phone, extract_address,
    should_skip_line, extract_store_name, LINE_ITEM_PATTERNS
)
try:
    import easyocr
except ImportError:
    easyocr=None
logger=logging.getLogger(__name__)

class EasyOCRProcessor:

    def __init__(self,model_config:Dict):
        self.model_config=model_config
        self.model_name=model_config['name']
        self.reader=None
        if easyocr is None:
            raise ImportError("EasyOCR not installed: pip install easyocr")
        try:
            logger.info("Initializing EasyOCR...")
            self.reader=easyocr.Reader(['en'],gpu=False)
            logger.info("EasyOCR initialized")
        except Exception as e:
            raise RuntimeError(f"EasyOCR init failed: {e}") from e

    def extract(self,image_path:str)->ExtractionResult:
        start_time=time.time()
        if easyocr is None:
            return ExtractionResult(success=False,error="EasyOCR not installed")
        if self.reader is None:
            return ExtractionResult(success=False,error="EasyOCR reader init failed")
        try:
            logger.info(f"EasyOCR: {image_path}")
            results=self.reader.readtext(image_path)
            logger.info(f"Detected {len(results)} regions")
            text_lines=[]
            for detection in results:
                if len(detection)>=3:
                    bbox,text,confidence=detection[0],detection[1],detection[2]
                    if confidence>0.3:
                        text_lines.append(text)
            if not text_lines:
                return ExtractionResult(success=False,error="No text detected")
            receipt=self._parse_receipt_text(text_lines)
            receipt.processing_time=time.time()-start_time
            receipt.model_used=self.model_name
            return ExtractionResult(success=True,data=receipt)
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}",exc_info=True)
            return ExtractionResult(success=False,error=str(e))

    def _parse_receipt_text(self,text_lines:List[str])->ReceiptData:
        receipt=ReceiptData()
        if not text_lines:
            receipt.extraction_notes.append("No text")
            return receipt
        receipt.store_name=extract_store_name(text_lines)
        receipt.transaction_date=extract_date(text_lines)
        receipt.total=extract_total(text_lines)
        receipt.items=self._extract_line_items(text_lines)
        receipt.store_address=extract_address(text_lines)
        receipt.store_phone=extract_phone(text_lines)
        return receipt

    def _extract_line_items(self,lines:List[str])->List[LineItem]:
        items,seen=[],set()
        for line in lines:
            if should_skip_line(line):
                continue
            for pattern in LINE_ITEM_PATTERNS:
                m=pattern.search(line.strip())
                if m:
                    name=m.group(1).strip()
                    price_str=m.group(2)
                    if len(name)<2 or name in seen:
                        continue
                    price=normalize_price(price_str)
                    if not price or price<=0:
                        continue
                    items.append(LineItem(name=name,total_price=price,quantity=1))
                    seen.add(name)
                    break
        return items

import numpy as np
from PIL import Image
from utils.image_processing import load_and_validate_image,preprocess_for_ocr

# Lazy import to allow mocking in tests
PaddleOCR = None

def _get_paddleocr():
    global PaddleOCR
    if PaddleOCR is None:
        try:
            from paddleocr import PaddleOCR as _PaddleOCR
            PaddleOCR = _PaddleOCR
        except ImportError:
            raise ImportError("paddleocr required: pip install paddleocr")
    return PaddleOCR

class PaddleProcessor:

    def __init__(self,model_config:Dict):
        self.model_config=model_config
        self.model_name=model_config['name']
        logger.info("Initializing PaddleOCR...")
        try:
            PaddleOCR = _get_paddleocr()
            self.ocr=PaddleOCR(use_angle_cls=True,lang='en',det_db_thresh=0.2,det_db_box_thresh=0.3)
            logger.info("PaddleOCR initialized")
        except Exception as e:
            logger.error(f"PaddleOCR init failed: {e}")
            raise

    def extract(self,image_path:str)->ExtractionResult:
        start_time=time.time()
        try:
            image=load_and_validate_image(image_path)
            preprocessed=preprocess_for_ocr(image,aggressive=True)
            image_np=np.array(preprocessed)
            if len(image_np.shape)==2:
                image_np=np.stack([image_np]*3,axis=-1)
                logger.info(f"Converted grayscale to RGB: {image_np.shape}")
            logger.info("Running PaddleOCR extraction...")
            result=self.ocr.ocr(image_np)
            logger.info(f"Result type:{type(result)}, len:{len(result) if result else 0}")
            if result and len(result)>0:
                logger.info(f"First elem: type={type(result[0])}, len={len(result[0]) if result[0] else 0}")
            if not result or not result[0]:
                logger.warning("No results, retrying with original image")
                image_np=np.array(image)
                result=self.ocr.ocr(image_np)
            if not result or not result[0]:
                logger.warning("PaddleOCR: no text detected")
                return ExtractionResult(success=False,error="No text detected")

            text_lines=[]
            for line in result[0]:
                if not line or len(line)<2:continue
                try:
                    bbox=line[0]
                    text_info=line[1]
                    if not isinstance(bbox,(list,tuple)) or len(bbox)<1:continue
                    if isinstance(text_info,(tuple,list)) and len(text_info)==2:
                        text,confidence=text_info
                    elif isinstance(text_info,str):
                        text=text_info
                        confidence=1.0
                    else:continue
                    if confidence>0.3:
                        text_lines.append({'text':text,'confidence':confidence,'bbox':bbox})
                except (ValueError,TypeError,IndexError):continue
            def safe_get_y(d):
                try:
                    bbox=d['bbox']
                    if isinstance(bbox,(list,tuple)) and len(bbox)>0:
                        fp=bbox[0]
                        if isinstance(fp,(list,tuple)) and len(fp)>1:return fp[1]
                    return 0
                except:return 0
            text_lines=sorted(text_lines,key=safe_get_y)
            logger.info(f"Detected {len(text_lines)} lines")
            receipt=self._parse_receipt_text(text_lines)
            receipt.processing_time=time.time()-start_time
            receipt.model_used=self.model_name
            if text_lines:
                receipt.confidence_score=round(sum(l['confidence'] for l in text_lines)/len(text_lines),2)
            return ExtractionResult(success=True,data=receipt)
        except Exception as e:
            logger.error(f"Extraction failed: {e}",exc_info=True)
            return ExtractionResult(success=False,error=str(e))

    def _parse_receipt_text(self,text_lines:List[Dict])->ReceiptData:
        receipt=ReceiptData()
        if not text_lines:
            receipt.extraction_notes.append("No text")
            return receipt
        lines=[l['text'].strip() for l in text_lines]
        receipt.store_name=extract_store_name(lines)
        if receipt.store_name and len(receipt.store_name)<2:
            receipt.extraction_notes.append(f"Short name: '{receipt.store_name}'")
        receipt.transaction_date=extract_date(lines)
        if receipt.transaction_date:
            logger.info(f"Date: {receipt.transaction_date}")
        receipt.total=extract_total(lines)
        if receipt.total:
            logger.info(f"Total: {receipt.total}")
        receipt.items=self._extract_line_items(lines,text_lines)
        receipt.store_address=extract_address(lines)
        if receipt.store_address:
            logger.info(f"Address: {receipt.store_address}")
        receipt.store_phone=extract_phone(lines)
        if receipt.store_phone:
            logger.info(f"Phone: {receipt.store_phone}")
        return receipt

    def _extract_line_items(self,lines:List[str],text_lines:List[Dict])->List[LineItem]:
        items,seen=[],set()
        for i,line in enumerate(lines):
            if should_skip_line(line):
                continue
            matched=False
            for pattern in LINE_ITEM_PATTERNS:
                m=pattern.search(line.strip())
                if m:
                    name=m.group(1).strip()
                    price_str=m.group(2).replace(',','.')
                    if len(name)<2 or name in seen or name.replace(' ','').isdigit():
                        continue
                    price=normalize_price(price_str)
                    if not price:
                        continue
                    conf=text_lines[i].get('confidence') if i<len(text_lines) else None
                    if conf and conf<0.4:
                        continue
                    items.append(LineItem(name=name,total_price=price))
                    seen.add(name)
                    matched=True
                    break
            if not matched:
                pm=re.search(r'\$?\s*(\d+[.,]\d{2})(?!\d)',line)
                if pm:
                    price_str=pm.group(1).replace(',','.')
                    price=normalize_price(price_str)
                    if price:
                        name_part=line[:pm.start()].strip()
                        name_part=re.sub(r'^\d+\s*[x*]\s*','',name_part).strip()
                        if len(name_part)>=2 and name_part not in seen:
                            if not should_skip_line(name_part):
                                items.append(LineItem(name=name_part,total_price=price))
                                seen.add(name_part)
        logger.info(f"Extracted {len(items)} items")
        return items
