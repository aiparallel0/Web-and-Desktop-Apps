import os
os.environ.update({'TF_ENABLE_ONEDNN_OPTS':'0','TF_CPP_MIN_LOG_LEVEL':'3','TRANSFORMERS_VERBOSITY':'error'})
import sys,json,re,logging,time
from decimal import Decimal
from typing import Dict,List,Optional
from PIL import Image
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from utils.data_structures import LineItem,ReceiptData,ExtractionResult
from utils.image_processing import load_and_validate_image,enhance_image

logger=logging.getLogger(__name__)

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
    def extract(self,image_path:str)->ExtractionResult:
        start_time=time.time()
        try:
            logger.info("Florence-2: Loading image...")
            image=load_and_validate_image(image_path)
            if image is None:raise ValueError("Image is None after loading")
            logger.info(f"Florence-2: Image loaded successfully, size: {image.size}")
            logger.info("Florence-2: Processing with model...")
            try:
                inputs=self.processor(text=self.task_prompt,images=image,return_tensors="pt")
                if inputs is None:raise ValueError("Processor returned None")
                logger.info(f"Florence-2: Inputs prepared, keys: {inputs.keys()}")
                inputs=inputs.to(self.device)
            except Exception as e:
                logger.error(f"Florence-2: Failed during input processing: {e}",exc_info=True)
                raise
            logger.info("Florence-2: Generating output...")
            try:
                generated_ids=self.model.generate(input_ids=inputs["input_ids"],pixel_values=inputs["pixel_values"],max_new_tokens=256,num_beams=1,do_sample=False,use_cache=False,early_stopping=True,pad_token_id=self.processor.tokenizer.pad_token_id,)
            except Exception as e:
                logger.error(f"Florence-2: Failed during generation: {e}",exc_info=True)
                raise
            logger.info("Florence-2: Decoding output...")
            generated_text=self.processor.batch_decode(generated_ids,skip_special_tokens=False)[0]
            logger.info(f"Florence-2: Generated text length: {len(generated_text)}")
            logger.info("Florence-2: Post-processing generation...")
            try:
                parsed_output=self.processor.post_process_generation(generated_text,task=self.task_prompt,image_size=(image.width,image.height))
                logger.info(f"Florence-2: Parsed output keys: {parsed_output.keys()if parsed_output else'None'}")
            except Exception as e:
                logger.error(f"Florence-2: Failed during post-processing: {e}",exc_info=True)
                raise
            receipt=self._build_receipt_from_ocr(parsed_output)
            receipt.processing_time,receipt.model_used=time.time()-start_time,self.model_name
            return ExtractionResult(success=True,data=receipt)
        except Exception as e:
            logger.error(f"Florence-2 extraction failed: {e}",exc_info=True)
            return ExtractionResult(success=False,error=str(e))
    def _build_receipt_from_ocr(self,parsed_output:Dict)->ReceiptData:
        receipt=ReceiptData()
        ocr_result=parsed_output.get(self.task_prompt,{})
        texts=ocr_result.get('labels',[])
        all_text=' '.join(texts)
        total_pattern=r'total[:\s]*\$?(\d+\.\d{2})'
        total_match=re.search(total_pattern,all_text,re.IGNORECASE)
        if total_match:receipt.total=self.normalize_price(total_match.group(1))
        date_pattern=r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        date_match=re.search(date_pattern,all_text)
        if date_match:receipt.transaction_date=date_match.group(1)
        if texts:receipt.store_name=texts[0]
        receipt.extraction_notes.append("Basic Florence-2 OCR extraction")
        return receipt
