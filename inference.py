import torch
import re
from PIL import Image
from transformers import DonutProcessor, VisionEncoderDecoderModel
import io
import json

def model_fn(model_dir, context=None):
    print("this is model_dir: ", model_dir)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    processor = DonutProcessor.from_pretrained(model_dir)
    model = VisionEncoderDecoderModel.from_pretrained(model_dir)
    model.to(device)
    return model, processor, device

def input_fn(input_data, content_type, context=None):
    """Deserialize the input data."""
    if content_type == 'application/x-image' or content_type == 'application/octet-stream':
        image = Image.open(io.BytesIO(input_data))
        return image
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(data, model_data, context=None):
    """Apply the model to the input data."""
    model, processor, device = model_data

    # Preprocess the image
    pixel_values = processor(data, return_tensors="pt").pixel_values.to(device)
    
    # Run inference
    model.eval()
    with torch.no_grad():
        task_prompt = "<s_receipt>"
        decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids.to(device)
        generated_outputs = model.generate(
            pixel_values,
            decoder_input_ids=decoder_input_ids,
            max_length=model.config.decoder.max_position_embeddings, 
            pad_token_id=processor.tokenizer.pad_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            early_stopping=True,
            bad_words_ids=[[processor.tokenizer.unk_token_id]],
            return_dict_in_generate=True
        )
    
    # Decode the output
    decoded_text = processor.batch_decode(generated_outputs.sequences)[0]
    decoded_text = decoded_text.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
    decoded_text = re.sub(r"<.*?>", "", decoded_text, count=1).strip()

    prediction = {'result': decoded_text}
    return prediction

def output_fn(prediction, accept):
    """Serialize the prediction output."""
    if accept == 'application/json':
        return json.dumps(prediction), 'application/json'
    else:
        raise ValueError(f"Unsupported response content type: {accept}")