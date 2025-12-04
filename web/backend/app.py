"""
=============================================================================
RECEIPT EXTRACTION API - Enterprise Flask Backend
=============================================================================

Version:    2.0.0
Author:     Receipt Extractor Team

Architecture:
    - Flask REST API with CORS support
    - Multi-model OCR processing pipeline
    - Model finetuning capabilities
    - Batch processing support

=============================================================================
"""

# =============================================================================
# MODULE IMPORTS & CONFIGURATION
# =============================================================================

import os
import sys
import re
import logging
import time
import gc
import json
import threading
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
from pathlib import Path
import zipfile

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.models.manager import ModelManager
from shared.models.engine import ModelTrainer, DataAugmenter

# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Register module with Circular Exchange
if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="web.backend.app",
            file_path=__file__,
            description="Flask REST API backend for receipt extraction with multi-model OCR processing",
            dependencies=["shared.models.model_manager", "shared.models.ocr_config", 
                         "shared.circular_exchange"],
            exports=["app", "model_manager", "process_receipt"]
        ))
        logger.info("Flask app registered with Circular Exchange Framework")
    except Exception as e:
        logger.warning(f"Could not register with Circular Exchange: {e}")

# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = Flask(__name__)
CORS(app)

# Application configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['REQUEST_TIMEOUT'] = 3600  # 1 hour timeout

# Allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'}

# Initialize model manager with resource limits
model_manager = ModelManager(max_loaded_models=3)

# Storage for finetuning jobs
finetune_jobs = {}

# Register additional routes (auth)
# Note: Receipt routes are defined inline in this file (extract_receipt, extract_batch)
try:
    from auth import register_auth_routes
    register_auth_routes(app)
    logger.info("Auth API routes registered")
except ImportError as e:
    logger.warning(f"Could not register auth routes: {e}")

# Register billing routes
try:
    from billing import register_billing_routes
    register_billing_routes(app)
    logger.info("Billing API routes registered")
except ImportError as e:
    logger.warning(f"Could not register billing routes: {e}")

# Register quick extract routes (no auth required)
try:
    from api import quick_extract_bp
    app.register_blueprint(quick_extract_bp)
    logger.info("Quick extract API routes registered")
except ImportError as e:
    logger.warning(f"Could not register quick extract routes: {e}")

# Initialize telemetry (OpenTelemetry tracing and metrics)
try:
    from telemetry import setup_telemetry
    telemetry_enabled = setup_telemetry(app)
    if telemetry_enabled:
        logger.info("OpenTelemetry initialized")
except ImportError as e:
    logger.info(f"Telemetry not available: {e}")

# Initialize CEFR bridge for production integration
cefr_bridge = None
try:
    from telemetry.cefr_bridge import get_cefr_bridge
    cefr_bridge = get_cefr_bridge()
    if cefr_bridge.is_enabled():
        logger.info("CEFR bridge initialized")
except ImportError as e:
    logger.info(f"CEFR bridge not available: {e}")

# Initialize security headers
try:
    from security.headers import init_security_headers
    init_security_headers(app)
    logger.info("Security headers enabled")
except ImportError as e:
    logger.warning(f"Security headers not available: {e}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def allowed_file(filename: str) -> bool:
    """
    Check if a filename has an allowed extension.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def safe_delete_temp_file(file_path: str, max_retries: int = 3):
    """
    Safely delete a temporary file with retry logic.
    
    Args:
        file_path: Path to the file to delete
        max_retries: Maximum number of deletion attempts
    """
    if not os.path.exists(file_path):
        return
    
    for attempt in range(max_retries):
        try:
            gc.collect()
            if sys.platform == 'win32' and attempt > 0:
                time.sleep(0.1 * (attempt + 1))
            os.unlink(file_path)
            logger.debug(f"Successfully deleted temp file: {file_path}")
            return
        except PermissionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Temp file deletion attempt {attempt + 1} failed (retrying): {e}")
            else:
                logger.error(
                    f"Failed to delete temp file after {max_retries} attempts: {file_path}. "
                    f"OS will clean up on reboot. Error: {e}"
                )
        except Exception as e:
            logger.error(f"Unexpected error deleting temp file {file_path}: {e}")
            break


def create_error_response(
    error_message: str,
    error_type: str = 'UnknownError',
    status_code: int = 500,
    details: dict = None
):
    """
    Create a standardized error response.
    
    Args:
        error_message: Human-readable error message
        error_type: Error classification
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        'success': False,
        'error': {
            'type': error_type,
            'message': error_message,
            'timestamp': time.time()
        }
    }
    if details:
        response['error']['details'] = details
    return jsonify(response), status_code


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors."""
    max_size_mb = app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
    return create_error_response(
        f"File too large. Maximum file size is {max_size_mb:.0f}MB",
        error_type='FileTooLarge',
        status_code=413
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {error}")
    return create_error_response(
        'Internal server error occurred',
        error_type='InternalServerError',
        status_code=500
    )


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.route('/', methods=['GET'])
def index():
    """API root endpoint with documentation."""
    return jsonify({
        'service': 'Receipt Extraction API',
        'version': '1.1',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'models': '/api/models',
            'select_model': '/api/models/select (POST)',
            'extract': '/api/extract (POST)',
            'batch_extract': '/api/extract/batch (POST) - Extract with ALL models',
            'model_info': '/api/models/<model_id>/info',
            'unload_models': '/api/models/unload (POST)'
        },
        'documentation': 'Access /api/health for health check or /api/models to see available models'
    })
@app.route('/api/health',methods=['GET'])
def health_check():
 try:
  import psutil,platform
  memory=psutil.virtual_memory()
  disk=psutil.disk_usage('/')
  resource_stats=model_manager.get_resource_stats()
  health_data={'status':'healthy','service':'receipt-extraction-api','version':'2.0','timestamp':time.time(),'system':{'platform':platform.system(),'python_version':platform.python_version(),'cpu_count':psutil.cpu_count(),'memory_total_gb':round(memory.total/(1024**3),2),'memory_available_gb':round(memory.available/(1024**3),2),'memory_percent_used':memory.percent,'disk_total_gb':round(disk.total/(1024**3),2),'disk_free_gb':round(disk.free/(1024**3),2),'disk_percent_used':disk.percent},'models':resource_stats}
  if memory.percent>90:health_data['status']='degraded';health_data['warnings']=['Memory usage critical (>90%)']
  elif memory.percent>80:health_data['status']='warning';health_data['warnings']=['Memory usage high (>80%)']
  return jsonify(health_data)
 except ImportError:return jsonify({'status':'healthy','service':'receipt-extraction-api','version':'2.0','note':'Install psutil for detailed system metrics'})
 except Exception as e:logger.error(f"Health check error: {e}");return jsonify({'status':'unhealthy','service':'receipt-extraction-api','error':str(e)}),500

@app.route('/api/cefr/dashboard', methods=['GET'])
def cefr_dashboard():
    """Get CEFR dashboard data with model performance insights."""
    try:
        if cefr_bridge and cefr_bridge.is_enabled():
            data = cefr_bridge.get_dashboard_data()
            return jsonify({'success': True, **data})
        else:
            return jsonify({
                'success': True,
                'enabled': False,
                'message': 'CEFR integration not available'
            })
    except Exception as e:
        logger.error(f"CEFR dashboard error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cefr/model/<model_id>/health', methods=['GET'])
def cefr_model_health(model_id):
    """Get CEFR health status for a specific model."""
    try:
        if cefr_bridge and cefr_bridge.is_enabled():
            health = cefr_bridge.get_model_health(model_id)
            if health:
                return jsonify({'success': True, 'health': health})
            else:
                return jsonify({'success': True, 'health': None, 'message': 'No data available'})
        else:
            return jsonify({'success': False, 'error': 'CEFR not available'}), 503
    except Exception as e:
        logger.error(f"CEFR model health error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cefr/suggestions', methods=['GET'])
def cefr_suggestions():
    """Get improvement suggestions from CEFR."""
    try:
        if cefr_bridge and cefr_bridge.is_enabled():
            suggestions = cefr_bridge.get_improvement_suggestions()
            return jsonify({
                'success': True,
                'suggestions': [
                    {
                        'model_id': s.model_id,
                        'improvement_type': s.improvement_type,
                        'description': s.description,
                        'priority': s.priority,
                        'estimated_impact': s.estimated_impact
                    }
                    for s in suggestions
                ]
            })
        else:
            return jsonify({'success': False, 'error': 'CEFR not available'}), 503
    except Exception as e:
        logger.error(f"CEFR suggestions error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cefr/feedback', methods=['POST'])
def cefr_feedback():
    """Submit user feedback to CEFR for model improvement."""
    try:
        data = request.get_json()
        extraction_id = data.get('extraction_id')
        model_id = data.get('model_id')
        is_correct = data.get('is_correct', True)
        corrections = data.get('corrections')
        
        if not extraction_id or not model_id:
            return jsonify({'success': False, 'error': 'extraction_id and model_id required'}), 400
        
        if cefr_bridge and cefr_bridge.is_enabled():
            cefr_bridge.report_feedback(
                extraction_id=extraction_id,
                model_id=model_id,
                is_correct=is_correct,
                corrections=corrections
            )
            return jsonify({'success': True, 'message': 'Feedback recorded'})
        else:
            return jsonify({'success': True, 'message': 'Feedback recorded (CEFR not available)'})
    except Exception as e:
        logger.error(f"CEFR feedback error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/models',methods=['GET'])
def get_models():
 try:models=model_manager.get_available_models();current_model=model_manager.get_current_model();default_model=model_manager.get_default_model();return jsonify({'success':True,'models':models,'current_model':current_model,'default_model':default_model})
 except Exception as e:logger.error(f"Error getting models: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/models/select',methods=['POST'])
def select_model():
 try:
  data=request.get_json()
  model_id=data.get('model_id')
  if not model_id:return jsonify({'success':False,'error':'model_id is required'}),400
  if not isinstance(model_id,str):return jsonify({'success':False,'error':'model_id must be a string'}),400
  if len(model_id)>100:return jsonify({'success':False,'error':'model_id too long'}),400
  if not re.match(r'^[a-zA-Z0-9_-]+$',model_id):return jsonify({'success':False,'error':'model_id contains invalid characters'}),400
  success=model_manager.select_model(model_id)
  if success:return jsonify({'success':True,'model_id':model_id,'message':f'Model {model_id} selected successfully'})
  else:return jsonify({'success':False,'error':f'Model {model_id} not found'}),404
 except Exception as e:logger.error(f"Error selecting model: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/extract',methods=['POST'])
def extract_receipt():
 try:
  if 'image'not in request.files:return jsonify({'success':False,'error':'No image file provided'}),400
  file=request.files['image']
  if file.filename=='':return jsonify({'success':False,'error':'No file selected'}),400
  if not allowed_file(file.filename):return jsonify({'success':False,'error':f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}),400
  model_id=request.form.get('model_id')
  filename=secure_filename(file.filename)
  with tempfile.NamedTemporaryFile(delete=False,suffix=os.path.splitext(filename)[1])as temp_file:temp_path=temp_file.name;file.save(temp_path)
  try:
   processor=model_manager.get_processor(model_id)
   logger.info(f"Processing image with model: {model_manager.get_current_model()}")
   result=processor.extract(temp_path)
   return jsonify(result.to_dict())
  finally:safe_delete_temp_file(temp_path)
 except Exception as e:logger.error(f"Extraction error: {e}",exc_info=True);return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/extract/batch',methods=['POST'])
def extract_batch():
 try:
  if 'image'not in request.files:return jsonify({'success':False,'error':'No image file provided'}),400
  file=request.files['image']
  if file.filename=='':return jsonify({'success':False,'error':'No file selected'}),400
  if not allowed_file(file.filename):return jsonify({'success':False,'error':f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}),400
  filename=secure_filename(file.filename)
  with tempfile.NamedTemporaryFile(delete=False,suffix=os.path.splitext(filename)[1])as temp_file:temp_path=temp_file.name;file.save(temp_path)
  try:
   available_models=model_manager.get_available_models()
   logger.info(f"Running batch extraction with {len(available_models)} models")
   batch_results={'success':True,'image_filename':filename,'models_count':len(available_models),'results':{}}
   for model_info in available_models:
    model_id=model_info['id']
    model_name=model_info['name']
    logger.info(f"Processing with model: {model_name} ({model_id})")
    try:
     processor=model_manager.get_processor(model_id)
     result=processor.extract(temp_path)
     batch_results['results'][model_id]={'model_name':model_name,'model_id':model_id,'extraction':result.to_dict()}
     logger.info(f"✓ {model_name}: {'Success'if result.success else'Failed'}")
    except Exception as e:logger.error(f"Model {model_name} failed: {e}");batch_results['results'][model_id]={'model_name':model_name,'model_id':model_id,'extraction':{'success':False,'error':str(e)}}
   logger.info(f"Batch extraction complete: {len(batch_results['results'])} models processed")
   return jsonify(batch_results)
  finally:safe_delete_temp_file(temp_path)
 except Exception as e:logger.error(f"Batch extraction error: {e}",exc_info=True);return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/models/<model_id>/info',methods=['GET'])
def get_model_info(model_id):
 try:
  model_info=model_manager.get_model_info(model_id)
  if model_info:return jsonify({'success':True,'model':model_info})
  else:return jsonify({'success':False,'error':f'Model {model_id} not found'}),404
 except Exception as e:logger.error(f"Error getting model info: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/models/unload',methods=['POST'])
def unload_models():
 try:model_manager.unload_all_models();return jsonify({'success':True,'message':'All models unloaded successfully'})
 except Exception as e:logger.error(f"Error unloading models: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/extract/batch-multi',methods=['POST'])
def extract_batch_multi():
 try:
  if 'images'not in request.files:return jsonify({'success':False,'error':'No image files provided'}),400
  files=request.files.getlist('images')
  if not files or len(files)==0:return jsonify({'success':False,'error':'No files selected'}),400
  model_id=request.form.get('model_id')
  use_all_models=request.form.get('use_all_models','false').lower()=='true'
  temp_paths=[]
  try:
   batch_results={'success':True,'images_count':len(files),'results':[]}
   if use_all_models:
    available_models=model_manager.get_available_models()
    logger.info(f"Batch processing {len(files)} images with {len(available_models)} models")
    for file in files:
     if file.filename==''or not allowed_file(file.filename):continue
     filename=secure_filename(file.filename)
     with tempfile.NamedTemporaryFile(delete=False,suffix=os.path.splitext(filename)[1])as temp_file:temp_path=temp_file.name;file.save(temp_path);temp_paths.append(temp_path)
     file_results={'filename':filename,'models':{}}
     for model_info in available_models:
      mid=model_info['id']
      try:
       processor=model_manager.get_processor(mid)
       result=processor.extract(temp_path)
       file_results['models'][mid]={'model_name':model_info['name'],'extraction':result.to_dict()}
      except Exception as e:logger.error(f"Model {mid} failed on {filename}: {e}");file_results['models'][mid]={'model_name':model_info['name'],'extraction':{'success':False,'error':str(e)}}
     batch_results['results'].append(file_results)
     logger.info(f"Processed {filename} with {len(available_models)} models")
   else:
    for file in files:
     if file.filename==''or not allowed_file(file.filename):continue
     filename=secure_filename(file.filename)
     with tempfile.NamedTemporaryFile(delete=False,suffix=os.path.splitext(filename)[1])as temp_file:temp_path=temp_file.name;file.save(temp_path);temp_paths.append(temp_path)
     try:
      processor=model_manager.get_processor(model_id)
      result=processor.extract(temp_path)
      batch_results['results'].append({'filename':filename,'extraction':result.to_dict()})
      logger.info(f"Processed {filename}: {'Success'if result.success else'Failed'}")
     except Exception as e:logger.error(f"Failed to process {filename}: {e}");batch_results['results'].append({'filename':filename,'extraction':{'success':False,'error':str(e)}})
   return jsonify(batch_results)
  finally:
   for temp_path in temp_paths:safe_delete_temp_file(temp_path)
 except Exception as e:logger.error(f"Batch multi extraction error: {e}",exc_info=True);return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/finetune/prepare',methods=['POST'])
def prepare_finetune():
 try:
  data=request.get_json()
  model_id=data.get('model_id')
  mode=data.get('mode','local')
  config=data.get('config',{})
  if not model_id:return jsonify({'success':False,'error':'model_id is required'}),400
  job_id=f"ft_{model_id}_{int(time.time())}"
  finetune_jobs[job_id]={'status':'preparing','model_id':model_id,'mode':mode,'config':config,'created':time.time(),'training_data':[],'progress':0}
  logger.info(f"Created finetuning job {job_id} for model {model_id} in {mode} mode")
  return jsonify({'success':True,'job_id':job_id,'message':'Finetuning job created'})
 except Exception as e:logger.error(f"Error preparing finetune: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/finetune/<job_id>/add-data',methods=['POST'])
def add_finetune_data(job_id):
 try:
  if job_id not in finetune_jobs:return jsonify({'success':False,'error':'Job not found'}),404
  if 'images'not in request.files:return jsonify({'success':False,'error':'No image files provided'}),400
  files=request.files.getlist('images')
  labels=json.loads(request.form.get('labels','{}'))
  job=finetune_jobs[job_id]
  upload_dir=Path(tempfile.gettempdir())/job_id
  upload_dir.mkdir(exist_ok=True)
  for file in files:
   if file.filename==''or not allowed_file(file.filename):continue
   filename=secure_filename(file.filename)
   file_path=upload_dir/filename
   file.save(str(file_path))
   ground_truth=labels.get(filename,{})
   job['training_data'].append({'image':str(file_path),'truth':ground_truth,'filename':filename})
   logger.info(f"Added training data: {filename}")
  job['status']='data_ready'
  return jsonify({'success':True,'samples_added':len(files),'total_samples':len(job['training_data'])})
 except Exception as e:logger.error(f"Error adding finetune data: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/finetune/<job_id>/start',methods=['POST'])
def start_finetune(job_id):
 try:
  if job_id not in finetune_jobs:return jsonify({'success':False,'error':'Job not found'}),404
  job=finetune_jobs[job_id]
  if len(job['training_data'])<1:return jsonify({'success':False,'error':'Not enough training data'}),400
  try:
   import torch
   import transformers
  except ImportError:
   return jsonify({'success':False,'error':'Finetuning requires PyTorch and Transformers. Install with: pip install torch transformers accelerate sentencepiece'}),400
  job['status']='running'
  job['started']=time.time()
  data=request.get_json()or{}
  epochs=data.get('epochs',3)
  batch_size=data.get('batch_size',4)
  learning_rate=data.get('learning_rate',5e-5)
  def get_model_type(model_id):
   model_types={'donut_cord':'donut','donut_base':'donut','florence_v2':'florence','easyocr':'ocr','paddle':'ocr'}
   return model_types.get(model_id,model_id.split('_')[0]if'_'in model_id else'unknown')
  def run_finetuning():
   try:
    logger.info(f"Starting finetuning job {job_id} for model {job['model_id']}")
    trainer=ModelTrainer(job['model_id'],job['config'])
    for sample in job['training_data']:trainer.add_training_sample(sample['image'],sample['truth'])
    job['progress']=10
    if job['mode']=='local':
     try:
      model_type=get_model_type(job['model_id'])
      logger.info(f"Detected model type: {model_type}")
      if model_type=='donut':
       from shared.models.donut_finetuner import DonutFinetuner
       finetuner=DonutFinetuner(job['model_id'])
       job['progress']=20
       metrics=finetuner.train(job['training_data'],epochs=epochs,batch_size=batch_size,learning_rate=learning_rate,progress_callback=lambda p:job.update({'progress':20+int(p*0.7)}))
       job['progress']=90
       output_dir=Path(tempfile.gettempdir())/f"{job_id}_model"
       output_dir.mkdir(exist_ok=True)
       finetuner.save_model(str(output_dir))
       job['model_path']=str(output_dir)
      elif model_type=='florence':
       from shared.models.florence_finetuner import FlorenceFinetuner
       finetuner=FlorenceFinetuner(job['model_id'])
       job['progress']=20
       metrics=finetuner.train(job['training_data'],epochs=epochs,batch_size=batch_size,learning_rate=learning_rate,progress_callback=lambda p:job.update({'progress':20+int(p*0.7)}))
       job['progress']=90
       output_dir=Path(tempfile.gettempdir())/f"{job_id}_model"
       output_dir.mkdir(exist_ok=True)
       finetuner.save_model(str(output_dir))
       job['model_path']=str(output_dir)
      elif model_type=='ocr':
       ocr_type=job['model_id'].lower()
       if 'easy' in ocr_type:
        from shared.models.ocr_finetuner import EasyOCRFinetuner
        finetuner=EasyOCRFinetuner(job['model_id'])
       else:
        from shared.models.ocr_finetuner import PaddleOCRFinetuner
        finetuner=PaddleOCRFinetuner(job['model_id'])
       job['progress']=20
       metrics=finetuner.train(job['training_data'],epochs=epochs,batch_size=batch_size,learning_rate=learning_rate,progress_callback=lambda p:job.update({'progress':20+int(p*0.7)}))
       job['progress']=90
       output_dir=Path(tempfile.gettempdir())/f"{job_id}_model"
       output_dir.mkdir(exist_ok=True)
       finetuner.save_model(str(output_dir))
       job['model_path']=str(output_dir)
      else:
       raise Exception(f"Unknown model type '{model_type}' for model '{job['model_id']}'. Supported for finetuning: Donut models. To add support for other models, create appropriate finetuner classes.")
     except ImportError as e:
      raise Exception(f"Finetuning dependencies not installed: {e}. Run: pip install torch transformers accelerate sentencepiece")
    elif job['mode']=='cloud':
     job['progress']=30
     cloud_provider=job['config'].get('cloud_provider','huggingface')
     cloud_api_key=job['config'].get('cloud_api_key')
     if not cloud_api_key:
      raise Exception(f"Cloud API key required for {cloud_provider} training. Please provide the API key in the configuration.")
     try:
      from shared.services.cloud_finetuning import CloudFinetuningService
      if cloud_provider=='huggingface':
       from shared.services.cloud_finetuning import HuggingFaceTrainer
       trainer=HuggingFaceTrainer(token=cloud_api_key)
      elif cloud_provider=='replicate':
       from shared.services.cloud_finetuning import ReplicateTrainer
       trainer=ReplicateTrainer(token=cloud_api_key)
      elif cloud_provider=='runpod':
       from shared.services.cloud_finetuning import RunPodTrainer
       trainer=RunPodTrainer(api_key=cloud_api_key)
      else:
       raise Exception(f"Unsupported cloud provider: {cloud_provider}. Supported: huggingface, replicate, runpod")
      cloud_job=trainer.start_training(job['model_id'],job['training_data'],{'epochs':epochs,'batch_size':batch_size,'learning_rate':learning_rate})
      job['cloud_job_id']=cloud_job.job_id
      job['cloud_url']=f"https://{cloud_provider}.com/jobs/{cloud_job.job_id}"
      job['progress']=50
      metrics={'cloud_provider':cloud_provider,'cloud_job_id':cloud_job.job_id,'status':'submitted'}
     except ImportError as e:
      raise Exception(f"Cloud finetuning dependencies not installed: {e}. Run: pip install requests huggingface_hub")
    job['progress']=100
    job['status']='completed'
    job['metrics']=metrics
    job['completed']=time.time()
    logger.info(f"Finetuning job {job_id} completed")
   except Exception as e:logger.error(f"Finetuning job {job_id} failed: {e}",exc_info=True);job['status']='failed';job['error']=str(e)
  thread=threading.Thread(target=run_finetuning)
  thread.start()
  return jsonify({'success':True,'message':'Finetuning started','job_id':job_id})
 except Exception as e:logger.error(f"Error starting finetune: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/finetune/<job_id>/status',methods=['GET'])
def get_finetune_status(job_id):
 try:
  if job_id not in finetune_jobs:return jsonify({'success':False,'error':'Job not found'}),404
  job=finetune_jobs[job_id]
  return jsonify({'success':True,'job':{'id':job_id,'status':job['status'],'progress':job.get('progress',0),'metrics':job.get('metrics'),'error':job.get('error'),'model_path':job.get('model_path'),'cloud_url':job.get('cloud_url'),'samples_count':len(job.get('training_data',[]))}})
 except Exception as e:logger.error(f"Error getting finetune status: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/finetune/<job_id>/export',methods=['GET'])
def export_finetuned_model(job_id):
 try:
  if job_id not in finetune_jobs:return jsonify({'success':False,'error':'Job not found'}),404
  job=finetune_jobs[job_id]
  if job['status']!='completed':return jsonify({'success':False,'error':'Job not completed'}),400
  if 'model_path'not in job:return jsonify({'success':False,'error':'No model to export'}),400
  model_path=Path(job['model_path'])
  zip_path=Path(tempfile.gettempdir())/f"{job_id}_export.zip"
  with zipfile.ZipFile(str(zip_path),'w',zipfile.ZIP_DEFLATED)as zipf:
   for file in model_path.rglob('*'):
    if file.is_file():zipf.write(file,file.relative_to(model_path))
  return send_file(str(zip_path),as_attachment=True,download_name=f"finetuned_{job['model_id']}.zip")
 except Exception as e:logger.error(f"Error exporting model: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/finetune/jobs',methods=['GET'])
def list_finetune_jobs():
 try:
  jobs_list=[{'id':job_id,'model_id':job['model_id'],'status':job['status'],'progress':job.get('progress',0),'created':job['created'],'samples':len(job.get('training_data',[]))}for job_id,job in finetune_jobs.items()]
  return jsonify({'success':True,'jobs':jobs_list})
 except Exception as e:logger.error(f"Error listing jobs: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/cloud/list',methods=['POST'])
def list_cloud_files():
 try:
  data=request.get_json()
  provider=data.get('provider')
  credentials=data.get('credentials',{})
  path=data.get('path','/')
  if not provider:
   return jsonify({'success':False,'error':'Provider is required. Supported: google_drive, dropbox, s3'}),400
  from shared.services.cloud_storage import CloudStorageService,GoogleDriveProvider,DropboxProvider,S3Provider
  storage_service=CloudStorageService()
  if provider=='google_drive':
   if not credentials.get('access_token')and not credentials.get('client_id'):
    return jsonify({'success':False,'error':'Google Drive requires OAuth credentials. Provide access_token or client_id/client_secret.'}),400
   storage_service.configure_google_drive(credentials=credentials,access_token=credentials.get('access_token'),client_id=credentials.get('client_id'),client_secret=credentials.get('client_secret'))
  elif provider=='dropbox':
   if not credentials.get('access_token'):
    return jsonify({'success':False,'error':'Dropbox access_token required.'}),400
   storage_service.configure_dropbox(access_token=credentials.get('access_token'),app_key=credentials.get('app_key'),app_secret=credentials.get('app_secret'))
  elif provider=='s3':
   if not credentials.get('access_key_id')or not credentials.get('secret_access_key'):
    return jsonify({'success':False,'error':'S3 requires access_key_id and secret_access_key.'}),400
   storage_service.configure_s3(bucket=credentials.get('bucket'),access_key_id=credentials.get('access_key_id'),secret_access_key=credentials.get('secret_access_key'),region=credentials.get('region'))
  else:
   return jsonify({'success':False,'error':f'Unsupported provider: {provider}. Supported: google_drive, dropbox, s3'}),400
  files=storage_service.list_files(provider,path)
  files_list=[{'id':f.id,'name':f.name,'path':f.path,'size':f.size,'mime_type':f.mime_type,'modified_at':f.modified_at.isoformat()if f.modified_at else None,'is_folder':f.is_folder,'download_url':f.download_url}for f in files]
  return jsonify({'success':True,'files':files_list,'provider':provider,'path':path})
 except ImportError as e:
  logger.error(f"Cloud storage import error: {e}")
  return jsonify({'success':False,'error':f'Cloud storage dependencies not installed: {e}. See documentation for required packages.'}),500
 except Exception as e:logger.error(f"Error listing cloud files: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/cloud/download',methods=['POST'])
def download_cloud_file():
 try:
  data=request.get_json()
  provider=data.get('provider')
  file_id=data.get('file_id')
  credentials=data.get('credentials',{})
  if not provider or not file_id:
   return jsonify({'success':False,'error':'Provider and file_id are required.'}),400
  from shared.services.cloud_storage import CloudStorageService
  storage_service=CloudStorageService()
  if provider=='google_drive':
   storage_service.configure_google_drive(credentials=credentials,access_token=credentials.get('access_token'))
  elif provider=='dropbox':
   storage_service.configure_dropbox(access_token=credentials.get('access_token'))
  elif provider=='s3':
   storage_service.configure_s3(bucket=credentials.get('bucket'),access_key_id=credentials.get('access_key_id'),secret_access_key=credentials.get('secret_access_key'))
  else:
   return jsonify({'success':False,'error':f'Unsupported provider: {provider}'}),400
  with tempfile.NamedTemporaryFile(delete=False)as temp_file:
   local_path=temp_file.name
  storage_service.download_file(provider,file_id,local_path)
  return send_file(local_path,as_attachment=True)
 except ImportError as e:
  return jsonify({'success':False,'error':f'Cloud storage dependencies not installed: {e}'}),500
 except Exception as e:logger.error(f"Error downloading cloud file: {e}");return jsonify({'success':False,'error':str(e)}),500
@app.route('/api/cloud/auth',methods=['POST'])
def cloud_auth():
 try:
  data=request.get_json()
  provider=data.get('provider')
  auth_code=data.get('auth_code')
  credentials=data.get('credentials',{})
  if not provider:
   return jsonify({'success':False,'error':'Provider is required.'}),400
  from shared.services.cloud_storage import CloudStorageService
  storage_service=CloudStorageService()
  if provider=='google_drive':
   storage_service.configure_google_drive(client_id=credentials.get('client_id'),client_secret=credentials.get('client_secret'))
   result=storage_service.authenticate(provider,auth_code)
   return jsonify({'success':True,'auth':result})
  elif provider=='dropbox':
   storage_service.configure_dropbox(app_key=credentials.get('app_key'),app_secret=credentials.get('app_secret'))
   result=storage_service.authenticate(provider,auth_code)
   return jsonify({'success':True,'auth':result})
  else:
   return jsonify({'success':False,'error':f'OAuth not supported for provider: {provider}'}),400
 except Exception as e:logger.error(f"Error in cloud auth: {e}");return jsonify({'success':False,'error':str(e)}),500
if __name__=='__main__':logger.info("Starting Receipt Extraction API...");logger.info(f"Available models: {len(model_manager.get_available_models())}");debug_mode=os.environ.get('FLASK_DEBUG','False').lower()in('true','1','yes');app.run(host='0.0.0.0',port=5000,debug=debug_mode)
