import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys,json
class StructuredFormatter(logging.Formatter):
    def format(self,record):
        log_data={'timestamp':datetime.utcnow().isoformat(),'level':record.levelname,'logger':record.name,'message':record.getMessage(),'module':record.module,'function':record.funcName,'line':record.lineno}
        if record.exc_info:log_data['exception']=self.formatException(record.exc_info)
        if hasattr(record,'extra_fields'):log_data.update(record.extra_fields)
        return json.dumps(log_data)
class ColoredFormatter(logging.Formatter):
    COLORS={'DEBUG':'\033[36m','INFO':'\033[32m','WARNING':'\033[33m','ERROR':'\033[31m','CRITICAL':'\033[35m'}
    RESET='\033[0m'
    def format(self,record):
        levelname=record.levelname
        if levelname in self.COLORS:record.levelname=f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        formatted=super().format(record)
        record.levelname=levelname
        return formatted
def setup_logger(name:str,level:str='INFO',log_dir:str='logs',use_json:bool=False,console_output:bool=True)->logging.Logger:
    logger=logging.getLogger(name)
    logger.setLevel(getattr(logging,level.upper()))
    if logger.handlers:return logger
    log_path=Path(log_dir)
    log_path.mkdir(parents=True,exist_ok=True)
    log_file=log_path/f'{name.replace(".","_")}.log'
    file_handler=logging.handlers.RotatingFileHandler(log_file,maxBytes=10*1024*1024,backupCount=5)
    if console_output:console_handler=logging.StreamHandler(sys.stdout)
    if use_json:
        file_formatter,console_formatter=StructuredFormatter(),StructuredFormatter()
    else:
        file_formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
        console_formatter=ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    if console_output:
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    return logger
def get_logger(name:str)->logging.Logger:
    return logging.getLogger(name)
def log_with_context(logger:logging.Logger,level:str,message:str,**kwargs):
    extra={'extra_fields':kwargs}
    getattr(logger,level)(message,extra=extra)
if __name__=='__main__':
    logger=setup_logger('receipt_extractor',level='DEBUG',use_json=False)
    logger.debug('This is a debug message')
    logger.info('Application started')
    logger.warning('This is a warning')
    logger.error('An error occurred')
    json_logger=setup_logger('receipt_extractor_prod',level='INFO',use_json=True)
    log_with_context(json_logger,'info','Receipt processed',receipt_id='12345',model='florence2',processing_time=2.5)
    try:raise ValueError('Example error')
    except Exception as e:json_logger.exception('Error processing receipt')
