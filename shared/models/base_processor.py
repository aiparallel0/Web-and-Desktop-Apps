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
