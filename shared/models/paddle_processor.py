import os,sys,re,logging,time
from decimal import Decimal
from typing import Dict,List,Optional
from PIL import Image
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from utils.data_structures import LineItem,ReceiptData,ExtractionResult
from utils.image_processing import load_and_validate_image,preprocess_for_ocr
try:
    from paddleocr import PaddleOCR
except ImportError:
    raise ImportError("paddleocr required: pip install paddleocr")
logger=logging.getLogger(__name__)
PRICE_MIN,PRICE_MAX=0,9999

class PaddleProcessor:
    SKIP_KEYWORDS={'subtotal','total','cash','change','tax','payment','balance','thank','visit','welcome','receipt','cashier','card','debit','credit','approved','transaction','visa','mastercard','amex'}

    def __init__(self,model_config:Dict):
        self.model_config=model_config
        self.model_name=model_config['name']
        logger.info("Initializing PaddleOCR...")
        try:
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
        receipt.store_name=None
        for i,line in enumerate(lines[:5]):
            if len(line)>=2 and not line.isdigit():
                receipt.store_name=line
                logger.info(f"Store: {line}")
                break
        if not receipt.store_name and lines:
            receipt.store_name=lines[0]
            if len(receipt.store_name)<2:receipt.extraction_notes.append(f"Short name: '{receipt.store_name}'")
        date_patterns=[r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',r'(\w{3}\s+\d{1,2},?\s+\d{4})']
        for line in lines:
            for pattern in date_patterns:
                dm=re.search(pattern,line)
                if dm:
                    receipt.transaction_date=dm.group(1)
                    logger.info(f"Date: {receipt.transaction_date}")
                    break
            if receipt.transaction_date:break
        total_patterns=[r'total[:\s]*\$?\s*(\d+[.,]\d{2})',r'amount[:\s]*\$?\s*(\d+[.,]\d{2})',r'balance[:\s]*\$?\s*(\d+[.,]\d{2})',r'grand\s*total[:\s]*\$?\s*(\d+[.,]\d{2})']
        for pattern in total_patterns:
            for line in lines:
                m=re.search(pattern,line,re.IGNORECASE)
                if m:
                    total_str=m.group(1).replace(',','.')
                    total_val=self._normalize_price(total_str)
                    if total_val:
                        receipt.total=total_val
                        logger.info(f"Total: {receipt.total}")
                        break
            if receipt.total:break
        receipt.items=self._extract_line_items(lines,text_lines)
        addr_kw=['st','ave','rd','blvd','lane','drive','street','avenue','way','plaza']
        for line in lines[1:8]:
            ll=line.lower()
            if any(kw in ll for kw in addr_kw) and any(c.isdigit() for c in line):
                receipt.store_address=line
                logger.info(f"Address: {line}")
                break
        phone_patterns=[r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})']
        for line in lines:
            for pattern in phone_patterns:
                pm=re.search(pattern,line)
                if pm:
                    receipt.store_phone=pm.group(1)
                    logger.info(f"Phone: {receipt.store_phone}")
                    break
            if receipt.store_phone:break
        return receipt

    def _extract_line_items(self,lines:List[str],text_lines:List[Dict])->List[LineItem]:
        items,seen=[],set()
        patterns=[r'^(.+?)\s+\$?\s*(\d+[.,]\d{2})$',r'^(.+?)\s+(\d+[.,]\d{2})\s*$',r'^(.+?)\s+\$\s*(\d+[.,]\d{2})$']
        for i,line in enumerate(lines):
            ll=line.lower()
            if any(kw in ll for kw in self.SKIP_KEYWORDS):continue
            matched=False
            for pattern in patterns:
                m=re.search(pattern,line.strip())
                if m:
                    name=m.group(1).strip()
                    price_str=m.group(2).replace(',','.')
                    if len(name)<2 or name in seen or name.replace(' ','').isdigit():continue
                    price=self._normalize_price(price_str)
                    if not price:continue
                    conf=text_lines[i].get('confidence') if i<len(text_lines) else None
                    if conf and conf<0.4:continue
                    items.append(LineItem(name=name,total_price=price))
                    seen.add(name)
                    matched=True
                    break
            if not matched:
                pm=re.search(r'\$?\s*(\d+[.,]\d{2})(?!\d)',line)
                if pm:
                    price_str=pm.group(1).replace(',','.')
                    price=self._normalize_price(price_str)
                    if price:
                        name_part=line[:pm.start()].strip()
                        name_part=re.sub(r'^\d+\s*[x*]\s*','',name_part).strip()
                        if len(name_part)>=2 and name_part not in seen:
                            if not any(kw in name_part.lower() for kw in self.SKIP_KEYWORDS):
                                items.append(LineItem(name=name_part,total_price=price))
                                seen.add(name_part)
        logger.info(f"Extracted {len(items)} items")
        return items

    @staticmethod
    def _normalize_price(value)->Optional[Decimal]:
        if value is None:return None
        try:
            price_str=str(value).replace('$','').replace(',','.').replace(' ','').strip()
            if price_str.startswith('-'):return None
            val=Decimal(price_str)
            return val if PRICE_MIN<=val<=PRICE_MAX else None
        except (ValueError,ArithmeticError):return None
