import os,sys,json,logging
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from shared.models.model_manager import ModelManager
logging.basicConfig(level=logging.INFO,format='%(message)s')
logger=logging.getLogger(__name__)
if sys.platform=='win32':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
def main():
 if len(sys.argv)<2:print(json.dumps({'success':False,'error':'Usage: python process_receipt.py <image_path> [model_id]'}));sys.exit(1)
 image_path=sys.argv[1]
 model_id=sys.argv[2]if len(sys.argv)>2 else None
 if not os.path.exists(image_path):print(json.dumps({'success':False,'error':f'Image file not found: {image_path}'}));sys.exit(1)
 try:
  logger.info(f"Initializing model manager...")
  model_manager=ModelManager()
  if model_id:
   success=model_manager.select_model(model_id)
   if not success:print(json.dumps({'success':False,'error':f'Invalid model ID: {model_id}'}));sys.exit(1)
  else:model_id=model_manager.get_default_model();model_manager.select_model(model_id)
  logger.info(f"Using model: {model_id}")
  processor=model_manager.get_processor(model_id)
  logger.info(f"Processing image: {image_path}")
  result=processor.extract(image_path)
  print(json.dumps(result.to_dict()))
 except Exception as e:logger.error(f"Error: {e}",exc_info=True);print(json.dumps({'success':False,'error':str(e)}));sys.exit(1)
if __name__=='__main__':main()
