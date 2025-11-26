import os,sys,re,logging,time
from decimal import Decimal
from typing import Dict,List,Optional
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from utils.data_structures import LineItem,ReceiptData,ExtractionResult
try:
    import easyocr
except ImportError:
    easyocr=None
logger=logging.getLogger(__name__)
PRICE_MIN,PRICE_MAX=0,9999

class EasyOCRProcessor:
    SKIP_KEYWORDS={'subtotal','total','cash','change','tax','payment','balance','thank','visit','welcome','receipt','cashier','card','debit','credit','approved','transaction'}

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
        receipt.store_name=None
        for line in text_lines[:5]:
            line=line.strip()
            if len(line)>=2 and not line.isdigit():
                receipt.store_name=line
                break
        if not receipt.store_name and text_lines:
            receipt.store_name=text_lines[0]
        date_pattern=r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        for line in text_lines:
            m=re.search(date_pattern,line)
            if m:
                receipt.transaction_date=m.group(1)
                break
        total_patterns=[r'total[:\s]*\$?\s*(\d+\.?\d{0,2})',r'amount[:\s]*\$?\s*(\d+\.?\d{0,2})',r'balance[:\s]*\$?\s*(\d+\.?\d{0,2})',r'grand\s*total[:\s]*\$?\s*(\d+\.?\d{0,2})']
        for line in text_lines:
            for pattern in total_patterns:
                m=re.search(pattern,line,re.IGNORECASE)
                if m:
                    price_str=m.group(1)
                    price=self._normalize_price(price_str)
                    if price and price>0:
                        receipt.total=price
                        break
            if receipt.total:break
        receipt.items=self._extract_line_items(text_lines)
        addr_kw=['st','ave','rd','blvd','lane','drive','street','avenue']
        for line in text_lines[1:8]:
            ll=line.lower()
            if any(kw in ll for kw in addr_kw) and any(c.isdigit() for c in line):
                receipt.store_address=line
                break
        phone_pattern=r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        for line in text_lines:
            m=re.search(phone_pattern,line)
            if m:
                receipt.store_phone=m.group(1)
                break
        return receipt

    def _extract_line_items(self,lines:List[str])->List[LineItem]:
        items,seen=[],set()
        patterns=[r'^(.+?)\s+\$?\s*(\d+\.?\d{0,2})$',r'^(.+?)\s+(\d+\.?\d{0,2})\s*$']
        for line in lines:
            ll=line.lower()
            if any(kw in ll for kw in self.SKIP_KEYWORDS):continue
            for pattern in patterns:
                m=re.search(pattern,line.strip())
                if m:
                    name=m.group(1).strip()
                    price_str=m.group(2)
                    if len(name)<2 or name in seen:continue
                    price=self._normalize_price(price_str)
                    if not price or price<=0:continue
                    items.append(LineItem(name=name,total_price=price,quantity=1))
                    seen.add(name)
                    break
        return items

    @staticmethod
    def _normalize_price(value)->Optional[Decimal]:
        if value is None:return None
        try:
            price_str=str(value).replace('$','').replace(',','').strip()
            if not price_str or price_str.startswith('-'):return None
            val=Decimal(price_str)
            return val if PRICE_MIN<=val<=PRICE_MAX else None
        except (ValueError,ArithmeticError):return None
