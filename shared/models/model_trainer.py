import os,json,logging,time
from typing import Dict,List,Optional
from pathlib import Path
import numpy as np
logger=logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self,model_type:str,config:Dict):
        self.model_type=model_type
        self.config=config
        self.training_data=[]
        self.validation_data=[]

    def add_training_sample(self,image_path:str,ground_truth:Dict):
        self.training_data.append({'image':image_path,'truth':ground_truth})
        logger.info(f"Added training sample: {image_path}")

    def add_validation_sample(self,image_path:str,ground_truth:Dict):
        self.validation_data.append({'image':image_path,'truth':ground_truth})

    def fine_tune_paddle(self,epochs:int=5,batch_size:int=8):
        logger.info(f"Fine-tuning PaddleOCR with {len(self.training_data)} samples")
        if not self.training_data:
            raise ValueError("No training data provided")

    def evaluate_model(self)->Dict:
        if not self.validation_data:
            logger.warning("No validation data")
            return {}
        results={'accuracy':0.0,'precision':0.0,'recall':0.0}
        logger.info(f"Evaluation: {results}")
        return results

    def save_model(self,output_path:str):
        Path(output_path).parent.mkdir(parents=True,exist_ok=True)
        with open(output_path,'w') as f:
            json.dump({'type':self.model_type,'config':self.config,'samples':len(self.training_data)},f)
        logger.info(f"Model saved to {output_path}")

    def incremental_learn(self,feedback:Dict):
        logger.info(f"Incremental learning from feedback: {feedback.get('correction_type')}")
        if 'corrections' in feedback:
            for correction in feedback['corrections']:
                self.training_data.append({'correction':correction,'timestamp':time.time()})

class DataAugmenter:
    @staticmethod
    def augment_image(image_path:str,output_dir:str)->List[str]:
        from PIL import Image,ImageEnhance
        import cv2
        augmented_paths=[]
        img=Image.open(image_path)
        base_name=Path(image_path).stem
        rotations=[-5,-2,2,5]
        for angle in rotations:
            rotated=img.rotate(angle,fillcolor=(255,255,255))
            out_path=f"{output_dir}/{base_name}_rot{angle}.png"
            rotated.save(out_path)
            augmented_paths.append(out_path)
        brightness_factors=[0.8,0.9,1.1,1.2]
        for factor in brightness_factors:
            enhancer=ImageEnhance.Brightness(img)
            bright=enhancer.enhance(factor)
            out_path=f"{output_dir}/{base_name}_bright{int(factor*100)}.png"
            bright.save(out_path)
            augmented_paths.append(out_path)
        logger.info(f"Generated {len(augmented_paths)} augmented samples")
        return augmented_paths

class IncrementalModelDevelopment:
    def __init__(self,base_model_id:str):
        self.base_model_id=base_model_id
        self.iterations=[]
        self.performance_history=[]

    def create_iteration(self,name:str,changes:Dict)->str:
        iteration_id=f"{self.base_model_id}_v{len(self.iterations)+1}"
        self.iterations.append({'id':iteration_id,'name':name,'changes':changes,'created':time.time()})
        logger.info(f"Created iteration {iteration_id}: {name}")
        return iteration_id

    def log_performance(self,iteration_id:str,metrics:Dict):
        self.performance_history.append({'iteration':iteration_id,'metrics':metrics,'timestamp':time.time()})

    def get_best_iteration(self)->Optional[str]:
        if not self.performance_history:return None
        best=max(self.performance_history,key=lambda x:x['metrics'].get('accuracy',0))
        return best['iteration']

    def export_iteration(self,iteration_id:str,output_path:str):
        iteration=next((i for i in self.iterations if i['id']==iteration_id),None)
        if not iteration:raise ValueError(f"Iteration {iteration_id} not found")
        with open(output_path,'w') as f:
            json.dump(iteration,f,indent=2)
        logger.info(f"Exported iteration {iteration_id} to {output_path}")
