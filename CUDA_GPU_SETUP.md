# GPU Acceleration Setup Guide

Enable CUDA GPU acceleration for 10-50x faster AI model inference.

---

## 📋 **Prerequisites**

### **Check if you have an NVIDIA GPU**

```bash
# Windows (PowerShell)
Get-WmiObject Win32_VideoController | Select-Object Name

# Linux
lspci | grep -i nvidia

# Or check Device Manager (Windows) / System Settings (Linux)
```

**Supported GPUs**: NVIDIA GTX 1050 or newer, RTX series, Tesla, Quadro
**Not supported**: AMD GPUs, Intel integrated graphics, Apple Silicon

---

## 🎯 **Installation Steps**

### **Step 1: Check Current PyTorch Installation**

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')"
```

**Current Status** (likely shows):
```
PyTorch: 2.9.1
CUDA Available: False
CUDA Version: N/A
```

---

### **Step 2: Install NVIDIA CUDA Toolkit**

#### **Windows**

1. **Download CUDA Toolkit 12.1**:
   - Visit: https://developer.nvidia.com/cuda-downloads
   - Select: Windows → x86_64 → 11 → exe (network)
   - Download: ~3GB

2. **Install CUDA**:
   ```bash
   # Run the downloaded installer
   # Choose "Express Installation"
   # Wait 15-30 minutes
   ```

3. **Verify Installation**:
   ```bash
   nvcc --version
   # Should show: Cuda compilation tools, release 12.1
   ```

#### **Linux**

```bash
# Ubuntu/Debian
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-1

# Verify
nvcc --version
```

---

### **Step 3: Install cuDNN (Optional but Recommended)**

cuDNN provides optimized primitives for deep learning.

#### **Windows**

1. **Download cuDNN**:
   - Visit: https://developer.nvidia.com/cudnn
   - Requires NVIDIA Developer account (free)
   - Download: cuDNN v8.9.x for CUDA 12.x

2. **Install**:
   ```bash
   # Extract ZIP file
   # Copy files to CUDA installation directory:
   # cudnn/bin/* → C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin
   # cudnn/include/* → C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\include
   # cudnn/lib/* → C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\lib
   ```

#### **Linux**

```bash
# Download from nvidia.com/cudnn, then:
sudo dpkg -i cudnn-local-repo-*.deb
sudo cp /var/cudnn-local-repo-*/cudnn-local-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get install libcudnn8 libcudnn8-dev
```

---

### **Step 4: Uninstall CPU PyTorch**

```bash
pip uninstall torch torchvision torchaudio
```

---

### **Step 5: Install GPU-Enabled PyTorch**

#### **For CUDA 12.1** (Recommended)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### **For CUDA 11.8** (If you have older GPU)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Installation Size**: ~2.5GB download, ~8GB installed

---

### **Step 6: Verify GPU Installation**

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}'); print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB' if torch.cuda.is_available() else '')"
```

**Expected Output**:
```
PyTorch: 2.9.1+cu121
CUDA Available: True
CUDA Version: 12.1
GPU Name: NVIDIA GeForce RTX 3060
GPU Memory: 12.0 GB
```

---

## 🚀 **Performance Improvements**

### **Speed Comparison** (Receipt Extraction)

| Model | CPU (Intel i7) | GPU (RTX 3060) | Speedup |
|-------|---------------|----------------|---------|
| Tesseract OCR | 16s | N/A | 1x |
| EasyOCR | ~45s | ~3s | **15x** |
| PaddleOCR | ~14s | ~2s | **7x** |
| Donut CORD | 20s | 2s | **10x** |
| Florence-2 | 60s | 4s | **15x** |

---

## 🔧 **Troubleshooting**

### **Issue: "CUDA out of memory"**

**Solution**:
```python
# The app automatically handles this, but you can reduce model size:
# Edit shared/config/models_config.json
# Change florence2 to florence2-base (smaller model)
```

### **Issue: "CUDA driver version is insufficient"**

**Solution**:
```bash
# Update NVIDIA drivers
# Windows: GeForce Experience → Drivers → Check for Updates
# Linux: sudo apt-get install nvidia-driver-535
```

### **Issue: "torch.cuda.is_available() returns False"**

**Checklist**:
1. ✅ NVIDIA GPU present (`nvidia-smi` works)
2. ✅ CUDA Toolkit installed (`nvcc --version` works)
3. ✅ GPU PyTorch installed (check `pip list | grep torch`)
4. ✅ Restart terminal/IDE after installation
5. ✅ Environment variables set (usually automatic)

**Manual environment check** (Windows):
```bash
echo %CUDA_PATH%
# Should show: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1
```

---

## 📊 **GPU Memory Requirements**

| Model | Min VRAM | Recommended VRAM |
|-------|----------|------------------|
| Tesseract | N/A | N/A (CPU only) |
| EasyOCR | 2GB | 4GB |
| PaddleOCR | 2GB | 4GB |
| Donut CORD | 4GB | 6GB |
| Florence-2-large | 6GB | 8GB |

**If you have 4GB VRAM**: Use EasyOCR, PaddleOCR, or Donut
**If you have 8GB+ VRAM**: Use Florence-2 for best quality

---

## 🎯 **Testing GPU Installation**

```bash
# Start the Flask server
cd web-app/backend
python app.py

# Check logs - should now show:
# "Model loaded successfully on cuda"
# Instead of: "on cpu"
```

**Before** (CPU):
```
2025-11-26 14:11:16 - INFO - Model loaded successfully on cpu
2025-11-26 14:11:38 - INFO - Processing completed in 21.6s
```

**After** (GPU):
```
2025-11-26 14:11:16 - INFO - Model loaded successfully on cuda
2025-11-26 14:11:18 - INFO - Processing completed in 2.1s
```

---

## 💰 **Cost/Benefit Analysis**

### **One-Time Setup Cost**
- Time: 1-2 hours
- Disk space: ~15GB (CUDA + PyTorch + models)
- Cost: $0 (all free software)

### **Performance Benefit**
- **10-15x faster** model inference
- Florence-2: 60s → 4s
- Donut CORD: 20s → 2s
- Better user experience
- Can process more receipts per minute

### **When It's Worth It**
- ✅ You have an NVIDIA GPU (GTX 1050+)
- ✅ You process many receipts (>10/day)
- ✅ You use AI models (Donut, Florence-2, EasyOCR)
- ❌ You only use Tesseract (CPU-only, no benefit)
- ❌ You have AMD/Intel GPU (not supported)

---

## 📚 **Additional Resources**

- **PyTorch CUDA Guide**: https://pytorch.org/get-started/locally/
- **CUDA Toolkit Docs**: https://docs.nvidia.com/cuda/
- **cuDNN Installation**: https://docs.nvidia.com/deeplearning/cudnn/install-guide/
- **GPU Memory Optimization**: https://pytorch.org/docs/stable/notes/cuda.html

---

## 🔄 **Reverting to CPU-Only**

If you want to go back to CPU-only:

```bash
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio
```

---

## ✅ **Quick Start Checklist**

- [ ] Verify NVIDIA GPU present
- [ ] Download & install CUDA Toolkit 12.1
- [ ] (Optional) Install cuDNN 8.9
- [ ] Uninstall CPU PyTorch
- [ ] Install GPU PyTorch (`pip install torch --index-url ...`)
- [ ] Verify with `torch.cuda.is_available()`
- [ ] Restart Flask server
- [ ] Check logs for "cuda" instead of "cpu"
- [ ] Test with receipt - should be 10x faster!

---

**Need help?** Check the troubleshooting section or the GitHub issues page.
