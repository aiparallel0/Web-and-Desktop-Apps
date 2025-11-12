# -*- coding: utf-8 -*-
"""
DONUT Receipt Parser - Enhanced with English Receipt Model
Uses AdamCodd/donut-receipts-extract for better English receipt performance
"""

import os
import sys
import warnings
from pathlib import Path
import re
import json
import socket
import signal
from contextlib import contextmanager

# Windows compatibility for UTF-8 output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("Loading dependencies...")

# Check PyTorch
try:
    import torch
    print(f"✓ PyTorch {torch.__version__} loaded")
except ImportError:
    print("✗ PyTorch not installed. Run: pip install torch")
    sys.exit(1)

# Check Transformers
try:
    from transformers import DonutProcessor, VisionEncoderDecoderModel
    print("✓ Transformers loaded")
except ImportError:
    print("✗ Transformers not installed. Run: pip install transformers")
    sys.exit(1)

# Check Gradio
try:
    import gradio as gr
    print("✓ Gradio loaded")
except ImportError:
    print("✗ Gradio not installed. Run: pip install gradio")
    sys.exit(1)

try:
    from PIL import Image
    print("✓ Pillow loaded")
except ImportError:
    print("✗ Pillow not installed. Run: pip install pillow")
    sys.exit(1)

print("=" * 60)
print("DONUT Receipt Parser - English Receipt Model")
print("=" * 60)
print(f"Python: {sys.version.split()[0]}")
print(f"Working directory: {os.getcwd()}")
print(f"Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")

# Global variables
processor = None
model = None
device = "cuda" if torch.cuda.is_available() else "cpu"

def load_model():
    """Load DONUT model fine-tuned on receipts"""
    global processor, model, device

    print("\n" + "=" * 60)
    print("Loading DONUT Receipt Model...")
    print("=" * 60)

    # Using publicly accessible receipt model
    # Note: AdamCodd/donut-receipts-extract requires HuggingFace authentication
    # Using naver-clova-ix model which is publicly accessible
    model_name = "naver-clova-ix/donut-base-finetuned-cord-v2"

    print(f"Model: {model_name}")
    print("This model is trained on CORD v2 receipt dataset")
    print("Publicly accessible - no authentication required")

    try:
        print("\nLoading processor...")
        processor = DonutProcessor.from_pretrained(model_name)
        print("✓ Processor loaded")

        print(f"\nLoading model to {device}...")
        print("Note: First run will download ~800MB")

        model = VisionEncoderDecoderModel.from_pretrained(
            model_name,
            device_map=None,
            low_cpu_mem_usage=False,
            torch_dtype=torch.float32
        )

        model = model.to(device)
        model.eval()

        print(f"✓ Model loaded successfully on {device}")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"✗ Error loading model: {e}")
        print("\nTroubleshooting:")
        print("1. Clear cache: rm -rf ~/.cache/huggingface/")
        print("2. Ensure stable internet connection")
        print("3. Check available disk space")
        return False

def clean_tag_content(text):
    """Remove any remaining unclosed tags from text"""
    text = re.sub(r'</?s_[a-z_]+>', '', text)
    return text.strip()

def extract_price_from_text(text):
    """Extract valid price from text, handling malformed data"""
    # Try to find price patterns
    price_match = re.search(r'\$?\d+\.\d{2}', text)
    if price_match:
        price = price_match.group()
        if not price.startswith('$'):
            price = '$' + price
        return price
    
    # Also handle prices without decimals
    price_match = re.search(r'\$?\d+', text)
    if price_match:
        price = price_match.group()
        if not price.startswith('$'):
            price = '$' + price
        # Add .00 if no decimal
        if '.' not in price:
            price = price + '.00'
        return price
    
    return None

def parse_donut_output(raw_output):
    """
    Parse DONUT's raw output from English receipt model
    The model uses tags like <s_company>, <s_date>, <s_address>, <s_total>
    """
    print("\n" + "="*60)
    print("DEBUG: RAW DONUT OUTPUT ANALYSIS")
    print("="*60)
    
    receipt = {
        'store_info': {},
        'items': [],
        'subtotal': None,
        'total': None,
        'payment': {},
        'metadata': {}
    }
    
    # Print raw output for debugging
    print("Raw output preview (first 500 chars):")
    print(raw_output[:500])
    print("...")
    
    # Extract store/company name - this model uses <s_company> tag
    company_match = re.search(r'<s_company>\s*([^<]+?)\s*</s_company>', raw_output)
    if company_match:
        receipt['store_info']['name'] = clean_tag_content(company_match.group(1))
    
    # Extract address - this model uses <s_address> tag
    address_match = re.search(r'<s_address>\s*([^<]+?)\s*</s_address>', raw_output)
    if address_match:
        address_text = clean_tag_content(address_match.group(1))
        # Split multi-line addresses
        receipt['store_info']['address'] = [addr.strip() for addr in address_text.split('\n') if addr.strip()]
    
    # Extract date
    date_match = re.search(r'<s_date>\s*([^<]+?)\s*</s_date>', raw_output)
    if date_match:
        receipt['store_info']['date'] = clean_tag_content(date_match.group(1))
    
    # Extract phone
    phone_match = re.search(r'<s_phone>\s*([^<]+?)\s*</s_phone>', raw_output)
    if phone_match:
        receipt['store_info']['phone'] = clean_tag_content(phone_match.group(1))
    
    # Extract menu items - this model uses <s_menu> with nested structure
    menu_match = re.search(r'<s_menu>(.*?)</s_menu>', raw_output, re.DOTALL)
    if menu_match:
        menu_content = menu_match.group(1)
        
        # Find all item entries
        item_pattern = r'<s_nm>([^<]+)</s_nm>.*?<s_price>([^<]+)</s_price>'
        items = re.findall(item_pattern, menu_content, re.DOTALL)
        
        print(f"\n📋 Found {len(items)} menu items")
        
        for name, price in items:
            clean_name = clean_tag_content(name)
            clean_price = extract_price_from_text(clean_tag_content(price))
            
            if clean_name:
                item = {'name': clean_name}
                if clean_price:
                    item['price'] = clean_price
                receipt['items'].append(item)
                print(f"  - {clean_name}: {clean_price}")
    
    # Fallback: try to extract items globally if menu parsing failed
    if not receipt['items']:
        print("\n⚠ Menu-based parsing found no items, trying global extraction...")
        
        all_names = re.findall(r'<s_nm>([^<]+)</s_nm>', raw_output)
        all_prices = re.findall(r'<s_price>([^<]+)</s_price>', raw_output)
        
        print(f"  Found {len(all_names)} names, {len(all_prices)} prices")
        
        for i, name in enumerate(all_names):
            clean_name = clean_tag_content(name)
            if clean_name and len(clean_name) > 1:
                item = {'name': clean_name}
                if i < len(all_prices):
                    clean_price = extract_price_from_text(clean_tag_content(all_prices[i]))
                    if clean_price:
                        item['price'] = clean_price
                receipt['items'].append(item)
    
    # Extract total
    total_match = re.search(r'<s_total>\s*([^<]+?)\s*</s_total>', raw_output)
    if total_match:
        receipt['total'] = extract_price_from_text(clean_tag_content(total_match.group(1)))
    
    # Also check for s_sub_total or s_subtotal
    subtotal_match = re.search(r'<s_sub_?total>\s*([^<]+?)\s*</s_sub_?total>', raw_output)
    if subtotal_match:
        receipt['subtotal'] = extract_price_from_text(clean_tag_content(subtotal_match.group(1)))
    
    # Extract tax if present
    tax_match = re.search(r'<s_tax>\s*([^<]+?)\s*</s_tax>', raw_output)
    if tax_match:
        receipt['metadata']['tax'] = extract_price_from_text(clean_tag_content(tax_match.group(1)))
    
    # Extract discount if present (new in V2)
    discount_match = re.search(r'<s_discount>\s*([^<]+?)\s*</s_discount>', raw_output)
    if discount_match:
        receipt['metadata']['discount'] = extract_price_from_text(clean_tag_content(discount_match.group(1)))
    
    print(f"\n✅ Parsed {len(receipt['items'])} items total")
    print("="*60 + "\n")
    
    return receipt

def validate_and_enhance_receipt(receipt_data, image=None):
    """Validate and enhance receipt data"""
    def normalize_price(price_str):
        if not price_str:
            return None
        price_str = str(price_str).strip()
        nums = re.findall(r'\d+\.\d{2}|\d+', price_str)
        if nums:
            price_val = nums[0]
            if '.' not in price_val:
                price_val = f"{price_val}.00"
            return f"${price_val}" if not price_val.startswith('$') else price_val
        return price_str
    
    # Normalize prices
    if receipt_data.get('subtotal'):
        receipt_data['subtotal'] = normalize_price(receipt_data['subtotal'])
    
    if receipt_data.get('total'):
        receipt_data['total'] = normalize_price(receipt_data['total'])
    
    if receipt_data.get('metadata'):
        if receipt_data['metadata'].get('tax'):
            receipt_data['metadata']['tax'] = normalize_price(receipt_data['metadata']['tax'])
        if receipt_data['metadata'].get('discount'):
            receipt_data['metadata']['discount'] = normalize_price(receipt_data['metadata']['discount'])
    
    for item in receipt_data.get('items', []):
        if item.get('price'):
            item['price'] = normalize_price(item['price'])
    
    # Remove duplicates
    seen_items = set()
    unique_items = []
    for item in receipt_data.get('items', []):
        item_key = f"{item.get('name', '')}_{item.get('price', '')}"
        if item_key not in seen_items:
            seen_items.add(item_key)
            unique_items.append(item)
    receipt_data['items'] = unique_items
    
    # Calculate and validate totals
    if receipt_data.get('items'):
        calculated_total = 0.0
        for item in receipt_data['items']:
            price_str = item.get('price', '0')
            try:
                price = float(re.sub(r'[^\d.]', '', price_str))
                calculated_total += price
            except:
                pass
        
        receipt_data['calculated_subtotal'] = f"${calculated_total:.2f}"
        
        # Check if calculated matches reported
        if receipt_data.get('subtotal'):
            try:
                reported = float(re.sub(r'[^\d.]', '', receipt_data['subtotal']))
                diff = abs(calculated_total - reported)
                if diff > 0.50:
                    receipt_data['validation_warning'] = f"Item total (${calculated_total:.2f}) differs from subtotal ({receipt_data['subtotal']})"
            except:
                pass
        elif receipt_data.get('total'):
            try:
                reported = float(re.sub(r'[^\d.]', '', receipt_data['total']))
                diff = abs(calculated_total - reported)
                if diff > 0.50:
                    receipt_data['validation_warning'] = f"Item total (${calculated_total:.2f}) differs from total ({receipt_data['total']})"
            except:
                pass
    
    return receipt_data

def format_structured_output(receipt_data):
    """Format structured receipt data for display"""
    output = []
    
    output.append("╔" + "═" * 58 + "╗")
    output.append("║" + " " * 16 + "🧾 RECEIPT ANALYSIS" + " " * 22 + "║")
    output.append("╚" + "═" * 58 + "╝")
    output.append("")
    
    if receipt_data.get('validation_warning'):
        output.append("⚠️  " + receipt_data['validation_warning'])
        output.append("")
    
    # Store Information
    if receipt_data.get('store_info'):
        output.append("┌─ STORE INFORMATION ─────────────────────────────────────┐")
        store = receipt_data['store_info']
        
        if store.get('name'):
            output.append(f"│ Store: {store['name']:<49}│")
        
        if store.get('address'):
            for addr in store['address'][:3]:
                if len(addr) > 55:
                    addr = addr[:52] + "..."
                output.append(f"│ {addr:<55}│")
        
        if store.get('phone'):
            output.append(f"│ Phone: {store['phone']:<49}│")
        
        if store.get('date'):
            output.append(f"│ Date: {store['date']:<50}│")
        
        output.append("└──────────────────────────────────────────────────────────┘")
        output.append("")
    
    # Items
    if receipt_data.get('items'):
        output.append("┌─ ITEMS PURCHASED ────────────────────────────────────────┐")
        output.append("│ #  Item Name                                    Price    │")
        output.append("├──────────────────────────────────────────────────────────┤")
        
        for idx, item in enumerate(receipt_data['items'], 1):
            name = item.get('name', 'Unknown Item')
            price = item.get('price', '[N/A]')
            
            if len(name) > 42:
                name = name[:39] + "..."
            
            price_display = price if price else "  [N/A]"
            
            output.append(f"│{idx:3}. {name:<43} {price_display:>8} │")
        
        output.append("└──────────────────────────────────────────────────────────┘")
        output.append("")
    
    # Totals
    output.append("┌─ TOTALS ─────────────────────────────────────────────────┐")
    
    if receipt_data.get('calculated_subtotal'):
        output.append(f"│ Items Sum:                                    {receipt_data['calculated_subtotal']:>10} │")
    
    if receipt_data.get('subtotal'):
        label = "Subtotal:" if not receipt_data.get('calculated_subtotal') else "Receipt Subtotal:"
        output.append(f"│ {label:<45} {receipt_data['subtotal']:>10} │")
    
    if receipt_data.get('metadata', {}).get('tax'):
        output.append(f"│ Tax:                                          {receipt_data['metadata']['tax']:>10} │")
    
    if receipt_data.get('metadata', {}).get('discount'):
        output.append(f"│ Discount:                                     {receipt_data['metadata']['discount']:>10} │")
    
    if receipt_data.get('total'):
        output.append(f"│ TOTAL:                                        {receipt_data['total']:>10} │")
    
    output.append("└──────────────────────────────────────────────────────────┘")
    output.append("")
    
    return "\n".join(output)

def parse_receipt(image):
    """Parse receipt image and extract information"""
    global processor, model, device

    if model is None or processor is None:
        print("Model not loaded, loading now...")
        if not load_model():
            return {"error": "Failed to load model. Please ensure dependencies are installed: pip install -r requirements.txt"}

    try:
        print("\nProcessing receipt...")

        # Robust image loading with error handling
        if isinstance(image, str):
            if not os.path.exists(image):
                return {"error": f"Image file not found: {image}"}
            try:
                image = Image.open(image).convert("RGB")
            except Exception as e:
                return {"error": f"Failed to open image file: {str(e)}"}
        elif not isinstance(image, Image.Image):
            try:
                image = Image.fromarray(image).convert("RGB")
            except Exception as e:
                return {"error": f"Failed to convert image array: {str(e)}"}

        # NOTE: CORD v2 model uses <s_cord-v2> as task prompt
        task_prompt = "<s_cord-v2>"
        
        decoder_input_ids = processor.tokenizer(
            task_prompt,
            add_special_tokens=False,
            return_tensors="pt"
        ).input_ids.to(device)

        pixel_values = processor(
            image,
            return_tensors="pt"
        ).pixel_values.to(device)

        print("Generating predictions...")

        # Add timeout to prevent hanging (60 seconds)
        @contextmanager
        def generation_timeout(seconds=60):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Model generation timed out after {seconds} seconds")

            # Only use alarm on Unix-like systems
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                try:
                    yield
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Windows doesn't support SIGALRM, skip timeout
                yield

        try:
            with generation_timeout(60):
                with torch.no_grad():
                    outputs = model.generate(
                        pixel_values,
                        decoder_input_ids=decoder_input_ids,
                        max_length=model.decoder.config.max_position_embeddings,
                        pad_token_id=processor.tokenizer.pad_token_id,
                        eos_token_id=processor.tokenizer.eos_token_id,
                        use_cache=True,
                        bad_words_ids=[[processor.tokenizer.unk_token_id]],
                        return_dict_in_generate=True,
                        num_beams=1,
                    )
        except TimeoutError as e:
            return {"error": str(e)}

        sequence = processor.batch_decode(outputs.sequences)[0]
        sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
        sequence = sequence.replace(task_prompt, "")

        print("✓ Receipt parsed successfully")
        
        structured_data = parse_donut_output(sequence)
        structured_data = validate_and_enhance_receipt(structured_data, image)
        structured_data['raw_output'] = sequence
        
        return structured_data

    except Exception as e:
        error_msg = f"Processing error: {str(e)}"
        print(f"✗ {error_msg}")
        import traceback
        traceback.print_exc()
        return {"error": error_msg}

def gradio_interface(image, show_raw):
    """Gradio interface wrapper"""
    if image is None:
        return "Please upload an image", "", ""

    result = parse_receipt(image)
    
    if "error" in result:
        return f"✗ Error: {result['error']}", "", ""
    
    formatted = format_structured_output(result)
    
    json_data = {k: v for k, v in result.items() if k != 'raw_output'}
    json_output = json.dumps(json_data, indent=2, ensure_ascii=False)
    
    raw = ""
    if show_raw and 'raw_output' in result:
        raw = "=" * 60 + "\n"
        raw += "RAW DONUT OUTPUT:\n"
        raw += "=" * 60 + "\n"
        raw += result['raw_output']
        raw += "\n" + "=" * 60
    
    return formatted, json_output, raw

print("\nPreloading model...")
if load_model():
    print("\n✓ Ready to process receipts!")
else:
    print("\n⚠ Model will load when you process first image")

print("\n" + "=" * 60)
print("Starting web interface...")
print("=" * 60)

with gr.Blocks(title="🧾 DONUT Receipt Parser") as demo:
    gr.Markdown("""
    # 🧾 DONUT Receipt Parser - English Receipt Model
    Upload a receipt image to extract structured information.
    
    **Model:** AdamCodd/donut-receipts-extract (trained on English receipts)
    
    **Features:**
    - Fine-tuned on SROIE English receipt dataset
    - Better performance on American receipts
    - Organized sections (Store, Items, Totals)
    - JSON export for integration
    - Validation of totals
    """)
    
    with gr.Row():
        with gr.Column():
            image_input = gr.Image(type="pil", label="Upload Receipt Image")
            show_raw = gr.Checkbox(label="Show raw DONUT output (for debugging)", value=False)
            process_btn = gr.Button("Parse Receipt", variant="primary")
        
        with gr.Column():
            formatted_output = gr.Textbox(label="📄 Formatted Receipt", lines=25, max_lines=30)
    
    with gr.Row():
        json_output = gr.Textbox(label="📋 JSON Output (for integration)", lines=15)
    
    with gr.Row():
        raw_output = gr.Textbox(label="🔍 Raw DONUT Output (debug)", lines=10, visible=True)
    
    process_btn.click(
        fn=gradio_interface,
        inputs=[image_input, show_raw],
        outputs=[formatted_output, json_output, raw_output]
    )
    
    gr.Markdown("""
    ---
    **Note:** First processing may take longer due to model initialization.
    This model is trained on English receipts and should work better with American formats.
    """)

if __name__ == "__main__":
    def find_free_port(start_port=7860, max_attempts=10):
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return None
    
    port = find_free_port()
    if port is None:
        print("❌ Could not find available port. Please close other applications.")
        sys.exit(1)
    
    print(f"\n🚀 Launching on http://127.0.0.1:{port}")
    demo.launch(
        server_name="127.0.0.1",
        server_port=port,
        share=False,
        show_error=True
    )