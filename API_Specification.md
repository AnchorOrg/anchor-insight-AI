# Anchor Insight AI - API Specification

## Overview

The Anchor Insight AI API is a FastAPI-based service that provides real-time human pose estimation using YOLOv11 models. The service accepts image data and returns processed images with pose annotations and keypoint data.

## Base Information

- **Framework**: FastAPI
- **Version**: 1.0.0
- **Base URL**: `http://localhost:8000`
- **Model**: YOLOv11-pose (yolo11s-pose.pt)
- **Content Type**: JSON, multipart/form-data
- **WebSocket Support**: Yes

## Authentication

Currently, no authentication is required for accessing the API endpoints.

## API Endpoints

### 1. Health Check

#### GET `/health`

Check the health status of the API service and model loading status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-07-02T10:30:00Z",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200`: Service is healthy
- `503`: Service unavailable (model not loaded)

---

### 2. Model Information

#### GET `/model/info`

Get information about the loaded YOLO model.

**Response:**
```json
{
  "model_name": "YOLOv11-pose",
  "model_path": "yolo11s-pose.pt",
  "model_loaded": true,
  "supported_classes": ["person"],
  "keypoints_count": 17,
  "input_size": [640, 640]
}
```

**Status Codes:**
- `200`: Model information retrieved successfully
- `404`: Model not found or not loaded

---

### 3. Pose Estimation (Single Image)

#### POST `/predict`

Perform pose estimation on a single image.

**Request Body (multipart/form-data):**
```
file: <image_file> (Required)
  - Type: File (JPEG, PNG, WebP)
  - Max size: 10MB
  
confidence: <float> (Optional, default: 0.5)
  - Type: Float
  - Range: 0.0 - 1.0
  - Description: Confidence threshold for detections

save_result: <boolean> (Optional, default: false)
  - Type: Boolean
  - Description: Whether to save the annotated result
```

**Response:**
```json
{
  "success": true,
  "detections": [
    {
      "id": 0,
      "class": "person",
      "confidence": 0.89,
      "bbox": {
        "x1": 100,
        "y1": 50,
        "x2": 300,
        "y2": 400
      },
      "keypoints": [
        {
          "id": 0,
          "name": "nose",
          "x": 200,
          "y": 80,
          "confidence": 0.95,
          "visible": true
        },
        {
          "id": 1,
          "name": "left_eye",
          "x": 190,
          "y": 75,
          "confidence": 0.92,
          "visible": true
        }
        // ... additional keypoints (17 total)
      ]
    }
  ],
  "annotated_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "processing_time": 0.124,
  "image_dimensions": {
    "width": 640,
    "height": 480
  }
}
```

**Status Codes:**
- `200`: Pose estimation successful
- `400`: Invalid image format or parameters
- `413`: Image file too large
- `422`: Validation error
- `500`: Internal server error

---

### 4. Pose Estimation (Base64 Image)

#### POST `/predict/base64`

Perform pose estimation on a base64-encoded image.

**Request Body (JSON):**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "confidence": 0.5,
  "save_result": false
}
```

**Response:** Same as `/predict` endpoint

**Status Codes:**
- `200`: Pose estimation successful
- `400`: Invalid base64 image or parameters
- `422`: Validation error
- `500`: Internal server error

---

### 5. Batch Pose Estimation

#### POST `/predict/batch`

Perform pose estimation on multiple images.

**Request Body (multipart/form-data):**
```
files: <image_files[]> (Required)
  - Type: Array of Files
  - Max files: 10
  - Max size per file: 10MB

confidence: <float> (Optional, default: 0.5)
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "filename": "image1.jpg",
      "detections": [...],
      "annotated_image": "data:image/jpeg;base64,...",
      "processing_time": 0.124
    },
    {
      "filename": "image2.jpg",
      "detections": [...],
      "annotated_image": "data:image/jpeg;base64,...",
      "processing_time": 0.098
    }
  ],
  "total_processing_time": 0.222,
  "processed_count": 2
}
```

**Status Codes:**
- `200`: Batch processing successful
- `400`: Invalid request or too many files
- `413`: Files too large
- `422`: Validation error

---

## WebSocket Endpoints

### Real-time Pose Estimation

#### WebSocket `/ws/pose`

Establish a WebSocket connection for real-time pose estimation.

**Connection URL:** `ws://localhost:8000/ws/pose`

**Client Messages:**
```json
{
  "type": "image",
  "data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "confidence": 0.5,
  "timestamp": "2025-07-02T10:30:00Z"
}
```

**Server Messages:**
```json
{
  "type": "pose_result",
  "data": {
    "detections": [...],
    "annotated_image": "data:image/jpeg;base64,...",
    "processing_time": 0.089,
    "timestamp": "2025-07-02T10:30:00Z"
  }
}
```

**Error Messages:**
```json
{
  "type": "error",
  "message": "Invalid image format",
  "code": "INVALID_IMAGE",
  "timestamp": "2025-07-02T10:30:00Z"
}
```

---

## Data Models

### Detection Object
```json
{
  "id": "integer",
  "class": "string",
  "confidence": "float (0.0-1.0)",
  "bbox": {
    "x1": "integer",
    "y1": "integer", 
    "x2": "integer",
    "y2": "integer"
  },
  "keypoints": "array of Keypoint objects"
}
```

### Keypoint Object
```json
{
  "id": "integer (0-16)",
  "name": "string",
  "x": "integer",
  "y": "integer", 
  "confidence": "float (0.0-1.0)",
  "visible": "boolean"
}
```

### Standard Keypoint Names (COCO Format)
1. nose
2. left_eye
3. right_eye
4. left_ear
5. right_ear
6. left_shoulder
7. right_shoulder
8. left_elbow
9. right_elbow
10. left_wrist
11. right_wrist
12. left_hip
13. right_hip
14. left_knee
15. right_knee
16. left_ankle
17. right_ankle

---

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details (optional)",
    "timestamp": "2025-07-02T10:30:00Z"
  }
}
```

### Common Error Codes
- `MODEL_NOT_LOADED`: YOLO model failed to load
- `INVALID_IMAGE`: Invalid image format or corrupted data
- `FILE_TOO_LARGE`: Uploaded file exceeds size limit
- `PROCESSING_ERROR`: Error during pose estimation
- `VALIDATION_ERROR`: Request validation failed
- `INTERNAL_ERROR`: Internal server error

---

## Rate Limiting

- **REST Endpoints**: 100 requests per minute per IP
- **WebSocket**: 30 messages per second per connection
- **Batch Endpoint**: 10 requests per minute per IP

---

## Usage Examples

### Python Client Example
```python
import requests
import base64

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Single image prediction
with open("person.jpg", "rb") as f:
    files = {"file": f}
    data = {"confidence": 0.7}
    response = requests.post("http://localhost:8000/predict", files=files, data=data)
    result = response.json()

# Base64 prediction
with open("person.jpg", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()
    data = {
        "image": f"data:image/jpeg;base64,{img_base64}",
        "confidence": 0.7
    }
    response = requests.post("http://localhost:8000/predict/base64", json=data)
    result = response.json()
```

### JavaScript WebSocket Example
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/pose');

ws.onopen = function() {
    console.log('WebSocket connected');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'pose_result') {
        // Handle pose estimation result
        console.log('Detections:', data.data.detections);
    }
};

// Send image for processing
function sendImage(imageBase64) {
    ws.send(JSON.stringify({
        type: 'image',
        data: imageBase64,
        confidence: 0.5,
        timestamp: new Date().toISOString()
    }));
}
```

---

## Performance Considerations

- **Image Preprocessing**: Images are automatically resized to optimal dimensions
- **GPU Acceleration**: CUDA support for faster inference (if available)
- **Memory Management**: Automatic cleanup of processed images
- **Concurrent Processing**: Support for multiple simultaneous requests
- **Caching**: Model weights cached in memory for faster subsequent requests

---

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
- `MODEL_PATH`: Path to YOLO model file (default: "./yolo11s-pose.pt")
- `MAX_FILE_SIZE`: Maximum upload file size in MB (default: 10)
- `CONFIDENCE_THRESHOLD`: Default confidence threshold (default: 0.5)
- `ENABLE_CORS`: Enable CORS for web clients (default: true)

---

## Security Considerations

- Input validation for all image uploads
- File type restrictions (JPEG, PNG, WebP only)
- File size limitations
- Rate limiting to prevent abuse
- CORS configuration for web security
- No sensitive data logging

---

## Monitoring and Logging

- Request/response logging
- Performance metrics (processing time, throughput)
- Error tracking and alerting
- Health check endpoints for monitoring systems
- Prometheus metrics endpoint available at `/metrics`

---

## Support and Contact

For technical support or questions about this API, please refer to the project documentation or create an issue in the project repository.
