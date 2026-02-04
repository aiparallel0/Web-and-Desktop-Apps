# Receipt Extractor API Documentation

## Overview

The Receipt Extractor API provides endpoints for extracting structured data from receipt images using AI-powered OCR models.

**Base URL:** `http://localhost:5000/api` (development) or your deployed URL

**Authentication:** JWT Bearer tokens for protected endpoints

---

## Authentication

### Register a New User

```http
POST /api/auth/register
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "company": "Acme Inc"
}
```

**Response (201):**
```json
{
    "success": true,
    "message": "Registration successful",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "full_name": "John Doe",
        "plan": "free"
    },
    "access_token": "eyJ...",
    "refresh_token": "xxx",
    "token_type": "Bearer",
    "expires_in": 900
}
```

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "SecurePass123!"
}
```

### Refresh Token

```http
POST /api/auth/refresh
Content-Type: application/json

{
    "refresh_token": "your_refresh_token"
}
```

### Get Current User

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

---

## Receipt Extraction

### Extract Single Receipt

Extract data from a single receipt image.

```http
POST /api/extract
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

image: <file>
model_id: easyocr (optional)
```

**Response (200):**
```json
{
    "success": true,
    "data": {
        "store": {
            "name": "Walmart",
            "address": "123 Main St",
            "phone": "555-1234"
        },
        "items": [
            {
                "name": "Milk 1 Gallon",
                "quantity": 1,
                "unit_price": 3.99,
                "total_price": 3.99
            }
        ],
        "totals": {
            "subtotal": 3.99,
            "tax": 0.35,
            "total": 4.34
        },
        "date": "2024-01-15",
        "time": "14:30",
        "payment_method": "VISA ****1234",
        "model": "easyocr",
        "processing_time": 1.23,
        "confidence": 0.95
    }
}
```

### Batch Extract (All Models)

Extract data from a single image using all available models.

```http
POST /api/extract/batch
Content-Type: multipart/form-data

image: <file>
```

**Response (200):**
```json
{
    "success": true,
    "image_filename": "receipt.jpg",
    "models_count": 4,
    "results": {
        "easyocr": {
            "model_name": "EasyOCR",
            "model_id": "easyocr",
            "extraction": { ... }
        },
        "tesseract": { ... },
        "donut_cord": { ... }
    }
}
```

### Batch Extract Multiple Images

Process multiple images at once.

```http
POST /api/extract/batch-multi
Content-Type: multipart/form-data

images: <file[]>
model_id: easyocr (optional)
use_all_models: true/false
```

---

## Models

### List Available Models

```http
GET /api/models
```

**Response:**
```json
{
    "success": true,
    "models": [
        {
            "id": "easyocr",
            "name": "EasyOCR",
            "type": "ocr",
            "description": "Neural network-based OCR",
            "capabilities": {
                "text_extraction": true,
                "structure_detection": true,
                "fine_tunable": true
            }
        }
    ],
    "current_model": "easyocr",
    "default_model": "easyocr"
}
```

### Select Model

```http
POST /api/models/select
Content-Type: application/json

{
    "model_id": "donut_cord"
}
```

### Get Model Info

```http
GET /api/models/<model_id>/info
```

### Unload All Models

Free up memory by unloading all loaded models.

```http
POST /api/models/unload
```

---

## Model Finetuning

### Prepare Finetuning Job

```http
POST /api/finetune/prepare
Content-Type: application/json

{
    "model_id": "donut_cord",
    "mode": "local",
    "config": {
        "epochs": 3,
        "batch_size": 4,
        "learning_rate": 0.00005
    }
}
```

### Add Training Data

```http
POST /api/finetune/<job_id>/add-data
Content-Type: multipart/form-data

images: <file[]>
labels: {"image1.jpg": {"store": "Test Store", "total": 10.99}}
```

### Start Finetuning

```http
POST /api/finetune/<job_id>/start
Content-Type: application/json

{
    "epochs": 3,
    "batch_size": 4,
    "learning_rate": 0.00005
}
```

### Get Finetuning Status

```http
GET /api/finetune/<job_id>/status
```

### Export Finetuned Model

```http
GET /api/finetune/<job_id>/export
```

Downloads the finetuned model as a ZIP file.

### List Finetuning Jobs

```http
GET /api/finetune/jobs
```

---

## Cloud Storage Integration

### List Cloud Files

```http
POST /api/cloud/list
Content-Type: application/json

{
    "provider": "google_drive",
    "credentials": {
        "access_token": "..."
    },
    "path": "/receipts"
}
```

### Download Cloud File

```http
POST /api/cloud/download
Content-Type: application/json

{
    "provider": "dropbox",
    "file_id": "file_path_or_id",
    "credentials": {
        "access_token": "..."
    }
}
```

---

## Billing

### Get Subscription Plans

```http
GET /api/billing/plans
```

### Get Current Subscription

```http
GET /api/billing/subscription
Authorization: Bearer <access_token>
```

### Get Usage Statistics

```http
GET /api/billing/usage
Authorization: Bearer <access_token>
```

### Create Checkout Session

```http
POST /api/billing/create-checkout
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "plan": "pro",
    "success_url": "https://yourapp.com/success",
    "cancel_url": "https://yourapp.com/cancel"
}
```

### Cancel Subscription

```http
POST /api/billing/cancel
Authorization: Bearer <access_token>
```

---

## Health & Status

### Health Check

The health check endpoint supports two modes:
- **Basic mode (default)**: Fast response for container health probes (~2ms)
- **Full mode**: Detailed system metrics for monitoring dashboards

#### Basic Health Check (Fast Mode)

```http
GET /api/health
```

**Response:**
```json
{
    "status": "healthy",
    "service": "receipt-extraction-api",
    "version": "2.0",
    "timestamp": 1699123456.789
}
```

**Response Time:** <100ms (typically ~2ms)

**Use Cases:**
- Container orchestration health probes (Docker, Kubernetes, Railway)
- Load balancer health checks
- Quick service availability checks

#### Full Health Check (Detailed Metrics)

```http
GET /api/health?full=true
```

**Response:**
```json
{
    "status": "healthy",
    "service": "receipt-extraction-api",
    "version": "2.0",
    "timestamp": 1699123456.789,
    "system": {
        "platform": "Linux",
        "python_version": "3.11.0",
        "cpu_count": 4,
        "memory_total_gb": 16.0,
        "memory_available_gb": 8.5,
        "memory_percent_used": 47.0,
        "disk_total_gb": 100.0,
        "disk_free_gb": 50.0,
        "disk_percent_used": 50.0
    },
    "models": {
        "loaded_models": 2,
        "max_loaded_models": 3,
        "available_models": ["ocr_tesseract", "ocr_easyocr"]
    }
}
```

**Response Time:** Variable (depends on system metrics collection)

**Use Cases:**
- Monitoring dashboards
- System health analysis
- Performance debugging

**Status Values:**
- `healthy`: System operating normally
- `warning`: Memory usage >80%
- `degraded`: Memory usage >90%
- `unhealthy`: Error occurred during health check

### Readiness Check

Lightweight endpoint for fast container readiness probes.

```http
GET /api/ready
```

**Response:**
```json
{
    "ready": true,
    "service": "receipt-extraction-api"
}
```

**Response Time:** <10ms (typically <1ms)

**Use Cases:**
- Container readiness probes
- Fastest possible health check
- Testing if Flask app is running

---

## Error Responses

All error responses follow this format:

```json
{
    "success": false,
    "error": {
        "type": "ValidationError",
        "message": "Human-readable error message",
        "timestamp": 1699123456.789,
        "details": {}
    }
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 413 | File Too Large |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

---

## Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| Authentication | 5 requests/minute |
| Extraction | 30 requests/minute |
| Batch Operations | 10 requests/minute |
| Finetuning | 5 requests/hour |
| General API | 100 requests/minute |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## SDKs and Client Libraries

### Python

```python
import requests

class ReceiptExtractorClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def extract(self, image_path, model_id=None):
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'model_id': model_id} if model_id else {}
            response = self.session.post(
                f'{self.base_url}/extract',
                files=files,
                data=data
            )
        return response.json()

# Usage
client = ReceiptExtractorClient('http://localhost:5000/api', 'your_token')
result = client.extract('receipt.jpg', model_id='easyocr')
```

### JavaScript/TypeScript

```javascript
class ReceiptExtractorClient {
    constructor(baseUrl, apiKey = null) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async extract(imageFile, modelId = null) {
        const formData = new FormData();
        formData.append('image', imageFile);
        if (modelId) formData.append('model_id', modelId);
        
        const response = await fetch(`${this.baseUrl}/extract`, {
            method: 'POST',
            headers: this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {},
            body: formData
        });
        
        return response.json();
    }
}

// Usage
const client = new ReceiptExtractorClient('http://localhost:5000/api', 'your_token');
const result = await client.extract(file, 'easyocr');
```

---

## Webhooks

Configure webhooks to receive notifications for:
- Extraction completed
- Finetuning job status changes
- Subscription events

Contact support for webhook configuration.
