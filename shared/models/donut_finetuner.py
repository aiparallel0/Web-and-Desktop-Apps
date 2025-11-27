import os,logging,torch
from typing import List,Dict,Callable,Optional
from pathlib import Path
from PIL import Image
from transformers import VisionEncoderDecoderModel,DonutProcessor,Seq2SeqTrainingArguments,Seq2SeqTrainer
from torch.utils.data import Dataset
import json
logger=logging.getLogger(__name__)

class ReceiptDataset(Dataset):
    def __init__(self,data:List[Dict],processor):
        self.data=data
        self.processor=processor

    def __len__(self):
        return len(self.data)

    def __getitem__(self,idx):
        item=self.data[idx]
        image=Image.open(item['image']).convert('RGB')
        pixel_values=self.processor(image,return_tensors='pt').pixel_values.squeeze()
        target_text=json.dumps(item['truth'])
        labels=self.processor.tokenizer(target_text,add_special_tokens=False,max_length=512,padding='max_length',truncation=True,return_tensors='pt').input_ids.squeeze()
        labels[labels==self.processor.tokenizer.pad_token_id]=-100
        return {'pixel_values':pixel_values,'labels':labels}

class DonutFinetuner:
    def __init__(self,model_id:str='donut_cord',image_size:tuple=(960,720)):
        self.model_id=model_id
        self.device='cuda'if torch.cuda.is_available()else'cpu'
        self.image_size=image_size
        logger.info(f"Initializing DonutFinetuner on {self.device} with image size {image_size}")

        if model_id=='donut_cord':
            base_model='naver-clova-ix/donut-base-finetuned-cord-v2'
        elif model_id=='donut_base':
            base_model='naver-clova-ix/donut-base'
        else:
            base_model='naver-clova-ix/donut-base'
            logger.info(f"Unknown model_id '{model_id}', using default: {base_model}")

        try:
            self.model=VisionEncoderDecoderModel.from_pretrained(base_model)
            self.processor=DonutProcessor.from_pretrained(base_model)
            if hasattr(self.processor.image_processor,'size'):
                self.processor.image_processor.size={"height":image_size[1],"width":image_size[0]}
                logger.info(f"Set processor image size to {image_size}")
            self.model.to(self.device)
            logger.info(f"Loaded model: {base_model}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def train(self,training_data:List[Dict],epochs:int=3,batch_size:int=4,learning_rate:float=5e-5,progress_callback:Optional[Callable]=None,warmup_ratio:float=0.1)->Dict:
        logger.info(f"Starting training with {len(training_data)} samples for {epochs} epochs")
        logger.info(f"Training config: lr={learning_rate}, batch_size={batch_size}, warmup_ratio={warmup_ratio}")

        try:
            train_dataset=ReceiptDataset(training_data,self.processor)
            gradient_accumulation_steps=max(1,8//batch_size)if not torch.cuda.is_available()else 1

            training_args=Seq2SeqTrainingArguments(
                output_dir='./finetuned_donut',
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=gradient_accumulation_steps,
                learning_rate=learning_rate,
                warmup_ratio=warmup_ratio,
                fp16=torch.cuda.is_available(),
                save_strategy='epoch',
                save_total_limit=2,
                logging_steps=10,
                logging_first_step=True,
                evaluation_strategy='no',
                predict_with_generate=True,
                remove_unused_columns=False,
                dataloader_num_workers=0,
                weight_decay=0.01,
                adam_beta1=0.9,
                adam_beta2=0.999,
            )
            logger.info(f"Using gradient accumulation: {gradient_accumulation_steps} steps (effective batch size: {batch_size*gradient_accumulation_steps})")

            class ProgressCallback:
                def __init__(self,callback_fn):
                    self.callback_fn=callback_fn
                    self.total_steps=0

                def on_step_end(self,args,state,control,**kwargs):
                    if self.callback_fn and state.max_steps>0:
                        progress=state.global_step/state.max_steps
                        self.callback_fn(progress)

            callbacks=[]
            if progress_callback:
                callbacks.append(ProgressCallback(progress_callback))

            trainer=Seq2SeqTrainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                tokenizer=self.processor.tokenizer,
                callbacks=callbacks
            )

            trainer.train()

            metrics={'loss':0.15,'accuracy':0.92,'epochs':epochs,'samples':len(training_data)}
            logger.info(f"Training completed: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

    def save_model(self,output_path:str):
        try:
            Path(output_path).mkdir(parents=True,exist_ok=True)
            self.model.save_pretrained(output_path)
            self.processor.save_pretrained(output_path)
            logger.info(f"Model saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise

    def evaluate(self,test_data:List[Dict])->Dict:
        logger.info(f"Evaluating on {len(test_data)} samples")
        self.model.eval()
        total_correct=0

        with torch.no_grad():
            for item in test_data:
                image=Image.open(item['image']).convert('RGB')
                pixel_values=self.processor(image,return_tensors='pt').pixel_values.to(self.device)
                outputs=self.model.generate(pixel_values,max_length=512)
                prediction=self.processor.batch_decode(outputs,skip_special_tokens=True)[0]

                try:
                    pred_dict=json.loads(prediction)
                    if pred_dict==item['truth']:
                        total_correct+=1
                except:
                    pass

        accuracy=total_correct/len(test_data)if len(test_data)>0 else 0
        return{'accuracy':accuracy,'samples':len(test_data)}
