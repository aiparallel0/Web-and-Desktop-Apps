#!/usr/bin/env python3
"""Quick test and model download utility"""
import sys, os

def check_env():
    try:
        import torch, transformers, PIL, cv2, numpy
        print("✓ Python environment OK")
        print(f"  PyTorch: {torch.__version__}")
        print(f"  GPU: {'Yes' if torch.cuda.is_available() else 'No'}")
        return True
    except ImportError as e:
        print(f"✗ Missing: {e}")
        print("Run: pip install torch transformers pillow opencv-python numpy")
        return False

def download_models():
    try:
        from transformers import DonutProcessor, VisionEncoderDecoderModel, AutoProcessor, AutoModelForCausalLM
        import torch

        models = [
            ('sroie', 'philschmid/donut-base-sroie', 'donut'),
            ('florence2', 'microsoft/Florence-2-large', 'florence')
        ]

        for name, repo, mtype in models:
            print(f"\nDownloading {name}...")
            try:
                if mtype == 'donut':
                    DonutProcessor.from_pretrained(repo)
                    VisionEncoderDecoderModel.from_pretrained(repo)
                else:
                    AutoModelForCausalLM.from_pretrained(repo, trust_remote_code=True)
                    AutoProcessor.from_pretrained(repo, trust_remote_code=True)
                print(f"✓ {name} ready")
            except Exception as e:
                print(f"✗ {name} failed: {e}")
    except Exception as e:
        print(f"Download failed: {e}")

if __name__ == '__main__':
    if '--download' in sys.argv:
        download_models()
    else:
        check_env()
