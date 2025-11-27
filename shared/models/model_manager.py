import os,json,logging,threading
from typing import Optional,Dict,List
from pathlib import Path
from datetime import datetime
logger=logging.getLogger(__name__)
class ModelManager:
    def __init__(self,config_path:Optional[str]=None,max_loaded_models:int=3):
        if config_path is None:config_path=Path(__file__).parent.parent/"config"/"models_config.json"
        self.config_path=config_path
        self.models_config=self._load_config()
        self.current_model=None
        self.loaded_processors={}
        self._lock=threading.RLock()
        self.max_loaded_models,self.model_last_used,self.model_load_times=max_loaded_models,{},{}
        self._check_gpu_availability()
    def _load_config(self)->dict:
        try:
            with open(self.config_path,'r')as f:config=json.load(f)
            self._validate_config(config)
            logger.info(f"Loaded {len(config['available_models'])} model configurations")
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in models config: {e}")
            raise ValueError(f"Models configuration is not valid JSON: {e}")from e
        except Exception as e:
            logger.error(f"Failed to load models config: {e}")
            raise
    def _validate_config(self,config:dict):
        if'available_models'not in config:raise ValueError("Missing required field 'available_models' in config")
        if'default_model'not in config:raise ValueError("Missing required field 'default_model' in config")
        if not isinstance(config['available_models'],dict):raise ValueError("'available_models' must be an object/dictionary")
        for model_id,model_config in config['available_models'].items():self._validate_model_config(model_id,model_config)
        default=config['default_model']
        if default not in config['available_models']:raise ValueError(f"default_model '{default}' not found in available_models")
        if'recommended_model'in config:
            recommended=config['recommended_model']
            if recommended not in config['available_models']:raise ValueError(f"recommended_model '{recommended}' not found in available_models")
        logger.info("Configuration validation passed")
    def _check_gpu_availability(self):
        try:
            import torch
            cuda_available=torch.cuda.is_available()
            if cuda_available:
                gpu_name=torch.cuda.get_device_name(0)
                gpu_memory=torch.cuda.get_device_properties(0).total_memory/(1024**3)
                cuda_version=torch.version.cuda
                logger.info(f"🚀 GPU ACCELERATION ENABLED")
                logger.info(f"   GPU: {gpu_name}")
                logger.info(f"   VRAM: {gpu_memory:.1f} GB")
                logger.info(f"   CUDA: {cuda_version}")
                logger.info(f"   AI models will run 10-15x faster!")
            else:
                logger.info("ℹ️  GPU NOT AVAILABLE - Running on CPU")
                logger.info("   AI models will be slower (10-60 seconds per receipt)")
                logger.info("   OCR engines (EasyOCR, Tesseract, PaddleOCR) still work fine on CPU")
        except ImportError:
            logger.info("ℹ️  PyTorch not installed - advanced AI models disabled")
            logger.info("   Basic OCR models (EasyOCR, Tesseract, PaddleOCR) are available")
            logger.info("   For AI models and finetuning: pip install torch transformers accelerate sentencepiece")
        except Exception as e:logger.debug(f"GPU check failed: {e}")
    def _validate_model_config(self,model_id:str,model_config:dict):
        required_fields=['id','name','type','description']
        for field in required_fields:
            if field not in model_config:raise ValueError(f"Model '{model_id}' missing required field '{field}'")
        valid_types=['donut','florence','ocr','easyocr','paddle']
        model_type=model_config['type']
        if model_type not in valid_types:raise ValueError(f"Model '{model_id}' has invalid type '{model_type}'. Must be one of: {valid_types}")
        if model_type in['donut','florence']:
            if'huggingface_id'not in model_config:raise ValueError(f"Model '{model_id}' of type '{model_type}' requires 'huggingface_id'")
            if'task_prompt'not in model_config:raise ValueError(f"Model '{model_id}' of type '{model_type}' requires 'task_prompt'")
    def get_available_models(self)->List[Dict]:
        models=[]
        for model_id,config in self.models_config['available_models'].items():
            models.append({'id':config['id'],'name':config['name'],'type':config['type'],'description':config['description'],'requires_auth':config.get('requires_auth',False),'capabilities':config.get('capabilities',{})})
        return models
    def get_model_info(self,model_id:str)->Optional[Dict]:
        return self.models_config['available_models'].get(model_id)
    def get_default_model(self)->str:
        return self.models_config.get('default_model','donut_sroie')
    def select_model(self,model_id:str)->bool:
        with self._lock:
            if model_id not in self.models_config['available_models']:
                logger.error(f"Model {model_id} not found in available models")
                return False
            self.current_model=model_id
            logger.info(f"Selected model: {model_id}")
            return True
    def get_current_model(self)->Optional[str]:
        return self.current_model
    def get_processor(self,model_id:Optional[str]=None):
        with self._lock:
            if model_id is None:model_id=self.current_model
            if model_id is None:
                model_id=self.get_default_model()
                self.current_model=model_id
            if model_id in self.loaded_processors:
                logger.info(f"Using cached processor for {model_id}")
                self.model_last_used[model_id]=datetime.now()
                return self.loaded_processors[model_id]
            if len(self.loaded_processors)>=self.max_loaded_models:self._evict_least_recently_used()
            model_config=self.get_model_info(model_id)
            if not model_config:raise ValueError(f"Model {model_id} not found")
            model_type=model_config['type']
            logger.info(f"Loading processor for {model_id} (type: {model_type})")
            try:
                if model_type=='donut':
                    try:
                        from .donut_processor import DonutProcessor
                        processor=DonutProcessor(model_config)
                    except ImportError as e:
                        raise ImportError(f"Donut models require PyTorch and Transformers. Install with: pip install torch transformers accelerate sentencepiece. Error: {e}")
                elif model_type=='florence':
                    try:
                        from .donut_processor import FlorenceProcessor
                        processor=FlorenceProcessor(model_config)
                    except ImportError as e:
                        raise ImportError(f"Florence models require PyTorch and Transformers. Install with: pip install torch transformers accelerate sentencepiece. Error: {e}")
                elif model_type=='ocr':
                    from .ocr_processor import OCRProcessor
                    processor=OCRProcessor(model_config)
                elif model_type=='easyocr':
                    from .easyocr_processor import EasyOCRProcessor
                    processor=EasyOCRProcessor(model_config)
                elif model_type=='paddle':
                    from .paddle_processor import PaddleProcessor
                    processor=PaddleProcessor(model_config)
                else:raise ValueError(f"Unknown model type: {model_type}")
                self.loaded_processors[model_id]=processor
                self.model_last_used[model_id],self.model_load_times[model_id]=datetime.now(),datetime.now()
                logger.info(f"✓ Loaded and cached processor for {model_id}")
                return processor
            except ImportError as e:
                logger.error(f"❌ Failed to load processor {model_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"❌ Failed to load processor {model_id}: {e}")
                raise
    def _evict_least_recently_used(self):
        if not self.model_last_used:return
        lru_model=min(self.model_last_used.items(),key=lambda x:x[1])[0]
        logger.info(f"Evicting least recently used model: {lru_model}")
        self.unload_model(lru_model)
    def unload_model(self,model_id:str):
        with self._lock:
            if model_id in self.loaded_processors:
                del self.loaded_processors[model_id]
                self.model_last_used.pop(model_id,None)
                self.model_load_times.pop(model_id,None)
                logger.info(f"Unloaded model: {model_id}")
                import gc
                gc.collect()
    def unload_all_models(self):
        with self._lock:
            self.loaded_processors.clear()
            self.model_last_used.clear()
            self.model_load_times.clear()
            logger.info("Unloaded all models")
            import gc
            gc.collect()
    def get_model_capabilities(self,model_id:str)->Dict:
        model_info=self.get_model_info(model_id)
        if model_info:return model_info.get('capabilities',{})
        return{}
    def filter_models_by_capability(self,capability:str)->List[str]:
        matching_models=[]
        for model_id,config in self.models_config['available_models'].items():
            if config.get('capabilities',{}).get(capability,False):matching_models.append(model_id)
        return matching_models
    def get_resource_stats(self)->Dict:
        with self._lock:
            stats={'loaded_models_count':len(self.loaded_processors),'max_loaded_models':self.max_loaded_models,'current_model':self.current_model,'loaded_models':list(self.loaded_processors.keys()),'model_usage':{}}
            for model_id in self.loaded_processors.keys():
                stats['model_usage'][model_id]={'loaded_at':self.model_load_times.get(model_id,'unknown'),'last_used':self.model_last_used.get(model_id,'unknown')}
            return stats
