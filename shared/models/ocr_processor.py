import os,sys,re,logging,time,subprocess
from decimal import Decimal
from typing import Dict,List,Optional
from PIL import Image,ImageEnhance,ImageFilter
import cv2,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from utils.data_structures import LineItem,ReceiptData,ExtractionResult
from utils.image_processing import load_and_validate_image,preprocess_for_ocr
try:
    import pytesseract
except ImportError:
    raise ImportError("pytesseract required: pip install pytesseract")
logger=logging.getLogger(__name__)
PRICE_MIN,PRICE_MAX=0,9999

class OCRProcessor:
    SKIP_KEYWORDS={'subtotal','total','cash','change','tax','payment','balance','thank','visit','welcome','receipt','cashier','card','debit','credit','approved','transaction'}

    def __init__(self,model_config:Dict):
        self.model_config=model_config
        self.model_name=model_config['name']
        self.tesseract_path=self._find_tesseract()
        if self.tesseract_path is None:
            raise EnvironmentError("Tesseract not installed. Install: https://github.com/UB-Mannheim/tesseract/wiki")
        if self.tesseract_path and self.tesseract_path!='tesseract':
            pytesseract.pytesseract.tesseract_cmd=self.tesseract_path
            logger.info(f"Tesseract: {self.tesseract_path}")
        self._verify_tesseract()

    def _verify_tesseract(self):
        try:
            version=pytesseract.get_tesseract_version()
            logger.info(f"Tesseract v{version}")
        except Exception as e:
            raise EnvironmentError(f"Tesseract not working: {e}") from e

    def _find_tesseract(self)->Optional[str]:
        logger.info("Searching Tesseract...")
        try:
            result=subprocess.run(['tesseract','--version'],capture_output=True,text=True,timeout=5)
            if result.returncode==0:return 'tesseract'
        except (subprocess.TimeoutExpired,FileNotFoundError):pass
        if sys.platform=='win32':
            paths=[r'C:\Program Files\Tesseract-OCR\tesseract.exe',r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe']
            for p in paths:
                if os.path.exists(p):return p
        elif sys.platform=='darwin':
            paths=['/usr/local/bin/tesseract','/opt/homebrew/bin/tesseract']
            for p in paths:
                if os.path.exists(p):return p
        else:
            paths=['/usr/bin/tesseract','/usr/local/bin/tesseract']
            for p in paths:
                if os.path.exists(p):return p
        return None

    def _aggressive_preprocess(self,image:Image.Image)->List[Image.Image]:
        preprocessed=[]
        img_np=np.array(image)
        upscaled=cv2.resize(img_np,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
        gray1=cv2.cvtColor(upscaled,cv2.COLOR_RGB2GRAY)
        denoised1=cv2.fastNlMeansDenoising(gray1,h=10)
        _,thresh1=cv2.threshold(denoised1,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        preprocessed.append(Image.fromarray(thresh1))
        gray2=cv2.cvtColor(img_np,cv2.COLOR_RGB2GRAY)
        adaptive=cv2.adaptiveThreshold(gray2,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
        preprocessed.append(Image.fromarray(adaptive))
        gray3=cv2.cvtColor(img_np,cv2.COLOR_RGB2GRAY)
        enhanced=Image.fromarray(gray3)
        enhancer=ImageEnhance.Contrast(enhanced)
        preprocessed.append(enhancer.enhance(2.0))
        return preprocessed

    def extract(self,image_path:str)->ExtractionResult:
        start_time=time.time()
        if not self.tesseract_path:
            return ExtractionResult(success=False,error="Tesseract not installed")
        try:
            image=load_and_validate_image(image_path)
            processed=preprocess_for_ocr(image,aggressive=True)
            ocr_results=[]
            config1=r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,:/\-#@()&% '
            text1=pytesseract.image_to_string(processed,lang='eng',config=config1)
            ocr_results.append(('PSM 6',text1))
            config2=r'--oem 3 --psm 4'
            text2=pytesseract.image_to_string(processed,lang='eng',config=config2)
            ocr_results.append(('PSM 4',text2))
            best_mode,best_text=max(ocr_results,key=lambda x:len(x[1].strip()))
            logger.info(f"OCR complete: {best_mode}, len={len(best_text)}")
            receipt=self._parse_receipt_text(best_text)
            receipt.processing_time=time.time()-start_time
            receipt.model_used=f"{self.model_name} ({best_mode})"
            if len(best_text.strip())<50:
                receipt.extraction_notes.append("Low OCR output - poor image quality")
            preprocessed_versions=self._aggressive_preprocess(image)
            psm_modes=[6,4,11,3]
            best_result,best_score=None,0
            for v_idx,proc_img in enumerate(preprocessed_versions):
                for psm in psm_modes:
                    try:
                        config=f'--oem 3 --psm {psm}'
                        text=pytesseract.image_to_string(proc_img,lang='eng',config=config)
                        if not text or len(text.strip())<10:continue
                        rec=self._parse_receipt_text(text)
                        score=self._score_result(rec,text)
                        if score>best_score:
                            best_score=score
                            best_result=rec
                    except:continue
            if best_result is None or best_score==0:
                return ExtractionResult(success=False,error="No readable text. Try EasyOCR.")
            best_result.processing_time=time.time()-start_time
            best_result.model_used=self.model_name
            best_result.confidence_score=min(1.0,best_score/95)
            return ExtractionResult(success=True,data=best_result)
        except Exception as e:
            logger.error(f"OCR failed: {e}",exc_info=True)
            return ExtractionResult(success=False,error=str(e))

    def _score_result(self,receipt:ReceiptData,text:str)->int:
        score=0
        if receipt.store_name and len(receipt.store_name)>2:score+=20
        if receipt.transaction_date:score+=15
        if receipt.total and receipt.total>0:score+=30
        if receipt.items:score+=10*len(receipt.items)
        if receipt.store_address:score+=10
        if receipt.store_phone:score+=10
        special_ratio=sum(1 for c in text if not c.isalnum() and not c.isspace())/max(len(text),1)
        if special_ratio>0.3:score-=20
        return max(0,score)

    def _parse_receipt_text(self,text:str)->ReceiptData:
        receipt=ReceiptData()
        lines=[line.strip() for line in text.split('\n') if line.strip()]
        if not lines:return receipt
        for line in lines[:5]:
            if len(line)>=3 and not line.isdigit():
                receipt.store_name=line
                break
        date_pattern=r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        for line in lines:
            m=re.search(date_pattern,line)
            if m:
                receipt.transaction_date=m.group(1)
                break
        total_patterns=[r'total[:\s]*\$?\s*(\d+\.?\d{0,2})',r'amount[:\s]*\$?\s*(\d+\.?\d{0,2})',r'balance[:\s]*\$?\s*(\d+\.?\d{0,2})',r'grand\s*total[:\s]*\$?\s*(\d+\.?\d{0,2})']
        for line in lines:
            for pattern in total_patterns:
                m=re.search(pattern,line,re.IGNORECASE)
                if m:
                    price=self._normalize_price(m.group(1))
                    if price and price>0:
                        receipt.total=price
                        break
            if receipt.total:break
        receipt.items=self._extract_line_items(lines)
        addr_kw=['st','ave','rd','blvd','lane','drive','street','avenue']
        for line in lines[1:8]:
            ll=line.lower()
            if any(kw in ll for kw in addr_kw) and any(c.isdigit() for c in line):
                receipt.store_address=line
                break
        phone_pattern=r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        for line in lines:
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
                    if len(name)<3 or name in seen:continue
                    alphas=sum(1 for c in name if c.isalpha())
                    digits=sum(1 for c in name if c.isdigit())
                    if digits>alphas:continue
                    if len(name)<5 and not name.replace(' ','').isalpha():continue
                    price=self._normalize_price(price_str)
                    if not price or price<=0 or price>1000:continue
                    skip_patterns=['store','thank','visit','phone','fax','email','open','hours','daily','am','pm']
                    if any(skip in name.lower() for skip in skip_patterns):continue
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
