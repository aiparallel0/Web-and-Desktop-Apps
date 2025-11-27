# Receipt Extractor Pro - Web Application

A professional web-based receipt extraction system with AI model finetuning, batch processing, and cloud storage integration.

## Features

- **Multi-Model Extraction**: Choose from Donut, Florence-2, Tesseract, EasyOCR, and PaddleOCR
- **Model Finetuning**: Train custom models on your specific receipt formats
- **Batch Processing**: Process multiple receipts at once from local or cloud storage
- **Cloud Integration**: Connect to Google Drive, Dropbox, and AWS S3
- **Real-time Progress**: Monitor extraction and training progress
- **Export Options**: JSON, CSV, and TXT formats
- **Responsive UI**: Modern, professional interface

## Quick Start

### 1. Install Dependencies

```bash
cd web-app/backend
pip install -r requirements.txt
```

**Note**: For full functionality, you may need system dependencies:
- Tesseract OCR: `sudo apt-get install tesseract-ocr` (Linux) or download from tesseract-ocr.github.io (Windows/Mac)
- CUDA toolkit for GPU acceleration (optional but recommended for finetuning)

### 2. Start Backend Server

```bash
cd web-app/backend
python app.py
```

The API server will start on `http://localhost:5000`

### 3. Open Frontend

Open `web-app/frontend/index.html` in your browser, or serve it using:

```bash
cd web-app/frontend
python -m http.server 8000
```

Then navigate to `http://localhost:8000`

## Usage Guide

### Basic Extraction

1. Navigate to the **Extract** tab
2. Select a model from the available options
3. Upload a receipt image (drag & drop or click to select)
4. Click **Extract Receipt Data**
5. View results and export if needed

### Batch Processing with Multiple Images

1. Go to the **Batch Processing** tab
2. Choose **Local Folder** source
3. Click to select multiple images (or drag & drop)
4. Click **Process All Images**
5. View individual results for each image
6. Export all results as JSON

### Using Cloud Storage

1. In **Batch Processing** tab, select **Cloud Storage**
2. Choose provider (Google Drive, Dropbox, or S3)
3. Browse available files (requires API credentials - see Configuration)
4. Select files and process

### Model Finetuning

#### Local Training

1. Navigate to **Finetune Model** tab
2. Select **Local Computer** mode
3. Configure training parameters:
   - **Epochs**: 3-5 for quick test, 10-20 for production
   - **Batch Size**: 4 (reduce to 2 if out of memory)
   - **Learning Rate**: 0.00005 (default is usually good)
4. Upload training images with receipts
5. Click **Start Finetuning**
6. Monitor progress in real-time
7. Export trained model when complete

#### Cloud Training

1. Select **Cloud-Based Training** mode
2. Choose cloud provider (HuggingFace, Replicate, or RunPod)
3. Enter your API key
4. Upload training images
5. Start training (will use cloud resources)

### Viewing Training Jobs

- Click **View Training Jobs** to see all finetuning tasks
- Check status: preparing, running, completed, or failed
- View progress percentage and sample counts
- Access completed models for export

## API Endpoints

### Extraction

```
GET  /api/models                    - List available models
POST /api/models/select             - Select a model
POST /api/extract                   - Extract from single image
POST /api/extract/batch             - Extract with all models
POST /api/extract/batch-multi       - Extract multiple images
```

### Finetuning

```
POST /api/finetune/prepare          - Create finetuning job
POST /api/finetune/{id}/add-data    - Upload training data
POST /api/finetune/{id}/start       - Start training
GET  /api/finetune/{id}/status      - Check training progress
GET  /api/finetune/{id}/export      - Download trained model
GET  /api/finetune/jobs             - List all jobs
```

### Cloud Storage

```
POST /api/cloud/list                - List cloud files
POST /api/cloud/download            - Download from cloud
```

### Health & Monitoring

```
GET  /api/health                    - System health check
GET  /api/models/{id}/info          - Model details
POST /api/models/unload             - Clear model cache
```

## Configuration

### Cloud Storage Setup

#### Google Drive

1. Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Google Drive API
3. Update backend with credentials
4. Set environment variables:
   ```bash
   export GOOGLE_CLIENT_ID="your_client_id"
   export GOOGLE_CLIENT_SECRET="your_secret"
   ```

#### Dropbox

1. Create app at [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Generate access token
3. Set environment variable:
   ```bash
   export DROPBOX_ACCESS_TOKEN="your_token"
   ```

#### AWS S3

1. Create IAM user with S3 read permissions
2. Generate access keys
3. Set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID="your_key"
   export AWS_SECRET_ACCESS_KEY="your_secret"
   export AWS_S3_BUCKET="your_bucket"
   ```

### Cloud Training Setup

#### HuggingFace

1. Sign up at [huggingface.co](https://huggingface.co)
2. Get API token from settings
3. Set environment variable:
   ```bash
   export HUGGINGFACE_TOKEN="your_token"
   ```

#### Replicate

1. Sign up at [replicate.com](https://replicate.com)
2. Get API token
3. Set environment variable:
   ```bash
   export REPLICATE_API_TOKEN="your_token"
   ```

## System Requirements

### Minimum

- Python 3.8+
- 8GB RAM
- 10GB disk space
- Modern web browser

### Recommended

- Python 3.10+
- 16GB RAM
- NVIDIA GPU with 8GB VRAM (for local finetuning)
- 50GB disk space (for models and training data)

### GPU Support

For GPU acceleration:
1. Install CUDA Toolkit (11.8 or 12.1)
2. Install cuDNN
3. Install PyTorch with CUDA:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

## Project Structure

```
web-app/
├── backend/
│   ├── app.py                  # Flask API server
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── index.html              # Main UI
│   ├── css/styles.css          # Styling
│   └── js/app.js               # Frontend logic
├── FINETUNING_GUIDE.md         # Detailed finetuning docs
└── README.md                   # This file
```

## Performance Tips

### For Extraction

1. Use appropriate model for your use case:
   - **Fast**: Tesseract, EasyOCR (1-2s per image)
   - **Accurate**: Donut, Florence-2 (5-10s per image)
   - **Balanced**: PaddleOCR (2-4s per image)

2. Enable GPU if available (3-5x faster)

3. Process in batches of 10-20 images for optimal throughput

### For Finetuning

1. Start with 20-30 high-quality labeled samples
2. Use GPU for training (10-20x faster)
3. Reduce batch size if running out of memory
4. Use mixed precision (FP16) for faster training
5. Monitor GPU usage with `nvidia-smi`

### For Production

1. Increase `max_loaded_models` in `ModelManager` for better caching
2. Use reverse proxy (nginx) for production deployment
3. Enable response compression
4. Set up rate limiting
5. Use persistent job storage (Redis/database) instead of in-memory dict

## Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError`
- **Solution**: Install dependencies with `pip install -r requirements.txt`

**Error**: `CUDA out of memory`
- **Solution**: Reduce batch size or use CPU mode

**Error**: `Port 5000 already in use`
- **Solution**: Kill existing process or change port in `app.py`

### Frontend Issues

**Error**: CORS errors in console
- **Solution**: Ensure backend is running and CORS is enabled

**Error**: Can't upload files
- **Solution**: Check file size < 100MB and format is supported

**Error**: Extraction fails
- **Solution**: Check backend logs, ensure model is loaded correctly

### Finetuning Issues

**Error**: Training won't start
- **Solution**:
  - Check GPU availability
  - Verify training images are uploaded
  - Check backend logs for errors

**Error**: Low accuracy after training
- **Solution**:
  - Increase training samples (aim for 50+)
  - Increase epochs (try 10-20)
  - Add more diverse receipt formats
  - Verify ground truth labels are correct

## Development

### Running in Development Mode

```bash
# Backend with auto-reload
export FLASK_DEBUG=True
python app.py

# Frontend with live server
cd frontend
python -m http.server 8000
```

### Testing

```bash
# Test single extraction
curl -X POST http://localhost:5000/api/extract \
  -F "image=@receipt.jpg" \
  -F "model_id=donut_cord"

# Test health endpoint
curl http://localhost:5000/api/health
```

### Adding New Models

1. Create processor class in `shared/models/`
2. Add model config to `shared/config/models_config.json`
3. Register in `ModelManager`
4. Update frontend model list

## Security Considerations

- File uploads are size-limited (100MB)
- File types are validated
- API keys should be stored in environment variables
- Use HTTPS in production
- Implement authentication for production deployment
- Sanitize all user inputs
- Set up request timeouts (default: 1 hour)

## Known Limitations

- Cloud storage integration is simulated (requires actual API implementation)
- In-memory job storage (lost on server restart)
- No user authentication (single-user mode)
- Model cache limited to 3 models (configurable)
- No distributed training support

## Future Enhancements

- [ ] User authentication and multi-tenancy
- [ ] Persistent job storage (database)
- [ ] Actual cloud storage API integration
- [ ] Real-time collaboration
- [ ] Model performance benchmarking
- [ ] A/B testing framework
- [ ] Active learning from corrections
- [ ] Multi-language support
- [ ] REST API documentation (Swagger)
- [ ] Docker containerization

## Support & Documentation

- **Finetuning Guide**: See `FINETUNING_GUIDE.md` for detailed training instructions
- **Main Project**: See root repository README for overall architecture
- **Issues**: Submit bugs and feature requests via GitHub Issues

## License

See main repository LICENSE file.

## Credits

Built with:
- Flask (Web framework)
- PyTorch (Deep learning)
- HuggingFace Transformers (Model library)
- Tesseract, EasyOCR, PaddleOCR (OCR engines)
- Modern vanilla JavaScript (Frontend)
