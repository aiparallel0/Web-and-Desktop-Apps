# Receipt Extractor Pro - Finetuning & Batch Processing Guide

## Overview

This enhanced version of the Receipt Extractor includes comprehensive finetuning capabilities, advanced batch processing, cloud storage integration, and improved UI for professional-grade receipt extraction workflows.

## New Features

### 1. Model Finetuning Interface

Train and customize AI models for your specific receipt formats and requirements.

#### Training Modes

**Local Computer Training**
- Train models on your own hardware
- Recommended: GPU with CUDA support (NVIDIA)
- Full control over training process
- No external costs
- Training parameters:
  - **Epochs**: Number of complete passes through training data (default: 3)
  - **Batch Size**: Number of samples per training batch (default: 4)
  - **Learning Rate**: Step size for model updates (default: 0.00005)

**Cloud-Based Training**
- Use paid cloud services for training
- Supported providers:
  - HuggingFace Spaces
  - Replicate
  - RunPod
- No local GPU required
- Faster training with powerful cloud GPUs
- Requires API key from chosen provider

#### How to Finetune a Model

1. Navigate to the **Finetune Model** tab
2. Select training mode (Local or Cloud)
3. Configure training parameters
4. Upload training images (multiple files supported)
5. Click **Start Finetuning**
6. Monitor progress in real-time
7. Export trained model when complete

### 2. Advanced Batch Processing

Process multiple receipt images efficiently with improved batch handling.

#### Features

**Local Folder Upload**
- Select multiple images at once (Ctrl/Cmd + Click)
- Folder selection support
- Drag-and-drop support
- File size display
- Progress tracking per image

**Cloud Storage Integration**
- Google Drive
- Dropbox
- AWS S3
- Browse and select files directly from cloud
- Download and process seamlessly

#### Batch Processing Workflow

1. Go to **Batch Processing** tab
2. Choose upload source:
   - **Local Folder**: Upload from your computer
   - **Cloud Storage**: Connect to cloud provider
3. Select images (multiple selection supported)
4. Click **Process All Images**
5. View results for each image
6. Export all results as JSON

#### Results Display

Each processed image shows:
- Filename
- Store name (if detected)
- Total amount
- Number of items extracted
- Processing time
- Success/Error status

### 3. Cloud Storage Integration

#### Supported Providers

**Google Drive**
- OAuth authentication
- Browse folders
- Select multiple files
- Direct download to processing

**Dropbox**
- API key authentication
- File browsing
- Batch selection
- Seamless integration

**AWS S3**
- Bucket configuration
- IAM credentials
- Object browsing
- Direct download

#### Setup Instructions

**Google Drive:**
1. Create OAuth credentials in Google Cloud Console
2. Enable Google Drive API
3. Enter credentials in app settings
4. Authorize access

**Dropbox:**
1. Create Dropbox App
2. Generate access token
3. Enter token in cloud settings
4. Browse files

**AWS S3:**
1. Create IAM user with S3 read permissions
2. Get Access Key ID and Secret Access Key
3. Configure bucket name
4. Enter credentials in settings

### 4. Export Functionality

#### Available Export Formats

**JSON Export**
- Full structured data
- All fields preserved
- Nested object structure
- Machine-readable

**CSV Export**
- Tabular format
- Line items with prices
- Store information
- Transaction details

**Text Export**
- Human-readable format
- Organized sections
- Easy to review
- Printable

**Batch Results Export**
- All images in single JSON file
- Timestamped filename
- Complete extraction data for all models
- Comparison-ready format

### 5. Training Job Management

#### View Training Jobs

Access all finetuning jobs through **View Training Jobs** button:
- Job ID and status
- Model being trained
- Progress percentage
- Sample count
- Creation timestamp
- Training metrics (when completed)

#### Job Statuses

- **Preparing**: Job created, waiting for data
- **Data Ready**: Training data uploaded
- **Running**: Model training in progress
- **Completed**: Training finished successfully
- **Failed**: Training encountered errors

### 6. Enhanced UI Features

#### Tab Navigation

Three main tabs for organized workflow:
- **Extract**: Single image extraction
- **Batch Processing**: Multiple images
- **Finetune Model**: Model training

#### Progress Tracking

Real-time progress indicators:
- Percentage-based progress bar
- Status messages
- Estimated completion (for cloud)
- Training metrics display

#### Results Visualization

Enhanced results display:
- Color-coded success/error states
- Detailed extraction information
- Processing statistics
- Export options

## API Endpoints

### Finetuning Endpoints

```
POST /api/finetune/prepare
Body: {model_id, mode, config}
Response: {job_id}

POST /api/finetune/{job_id}/add-data
Body: FormData with images and labels
Response: {samples_added, total_samples}

POST /api/finetune/{job_id}/start
Body: {epochs, batch_size, learning_rate}
Response: {success, message}

GET /api/finetune/{job_id}/status
Response: {status, progress, metrics, error}

GET /api/finetune/{job_id}/export
Response: ZIP file with trained model

GET /api/finetune/jobs
Response: {jobs: [{id, status, progress, ...}]}
```

### Batch Processing Endpoints

```
POST /api/extract/batch-multi
Body: FormData with multiple images
Response: {results: [{filename, extraction}]}

POST /api/extract/batch
Body: FormData with single image
Response: {results: {model_id: extraction}} (all models)
```

### Cloud Storage Endpoints

```
POST /api/cloud/list
Body: {provider, credentials, path}
Response: {files: [{name, path, size, type}]}

POST /api/cloud/download
Body: {provider, file_path, credentials}
Response: {local_path, filename}
```

## Technical Requirements

### Backend

- Python 3.8+
- Flask 2.0+
- PyTorch 2.0+ (for finetuning)
- Transformers 4.30+ (HuggingFace)
- 8GB+ RAM (16GB recommended)
- GPU with 6GB+ VRAM (for local training)

### Frontend

- Modern browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- 100MB file upload support
- LocalStorage for settings

### Optional Cloud Services

- HuggingFace account + API key
- Replicate account + API key
- RunPod account + API key
- Google Cloud account (for Drive)
- Dropbox developer account
- AWS account (for S3)

## Best Practices

### Training Data

1. **Quality over Quantity**: 20-30 high-quality labeled samples better than 100 poor ones
2. **Diversity**: Include various receipt formats, stores, lighting conditions
3. **Ground Truth**: Ensure labels are accurate and complete
4. **Image Quality**: Use clear, well-lit images without blur

### Batch Processing

1. **Consistent Format**: Group similar receipts for better results
2. **File Organization**: Name files systematically for easier tracking
3. **Size Management**: Keep batches under 50 images for optimal performance
4. **Result Review**: Always review automated results before export

### Model Selection

1. **Donut Models**: Best for structured receipt layouts
2. **OCR Models**: Good for simple text extraction
3. **Florence-2**: Excellent for complex layouts with images
4. **Custom Finetuned**: Best accuracy for specific receipt types

## Troubleshooting

### Finetuning Issues

**Problem**: Out of memory error
- **Solution**: Reduce batch size to 2 or 1
- Use smaller model variant
- Close other applications

**Problem**: Training not starting
- **Solution**: Check GPU availability
- Verify training data uploaded correctly
- Check API key (for cloud mode)

**Problem**: Poor accuracy after training
- **Solution**: Increase training samples
- Add more diverse data
- Increase epochs (to 5-10)
- Adjust learning rate

### Batch Processing Issues

**Problem**: Some images fail
- **Solution**: Check image format and quality
- Verify file sizes under limit
- Try individual extraction for failed images

**Problem**: Slow processing
- **Solution**: Reduce batch size
- Use faster model (OCR)
- Process in smaller groups

### Cloud Storage Issues

**Problem**: Can't connect to cloud
- **Solution**: Verify credentials
- Check API key validity
- Ensure proper permissions
- Test internet connection

## Performance Optimization

### For Local Training

1. Use GPU acceleration (CUDA)
2. Batch size 4-8 for 8GB VRAM
3. Mixed precision training (FP16)
4. Gradient accumulation for large batches

### For Batch Processing

1. Process in groups of 10-20 images
2. Use appropriate model for task
3. Enable parallel processing
4. Cache model in memory

## Security Considerations

1. **API Keys**: Never commit to version control
2. **Credentials**: Store securely (environment variables)
3. **Upload Limits**: Enforced at 100MB per file
4. **Timeout Protection**: 1-hour request timeout
5. **Input Validation**: All uploads sanitized

## Future Enhancements

- Active learning from corrections
- Multi-language support
- Custom model architectures
- Distributed training
- Real-time collaboration
- Automated data labeling
- Performance benchmarking
- A/B testing for models

## Support

For issues or questions:
1. Check this guide
2. Review API documentation
3. Check training job logs
4. Submit GitHub issue with details

## License

See main repository LICENSE file.
