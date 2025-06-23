# anchor-insight-AI

The application that is taking charge of AI related tasks mainly. 主にAI関連のタスクを担当するアプリケーション

## Overview

Anchor Insight AI provides real-time scoring and notifications based on user behavior analysis using computer vision and machine learning. The system analyzes camera input, screen captures, and user feedback to provide insights into focus, presence, and productivity.

## Features

### Input Processing
- **Camera Input**: Real-time camera feed processing using OpenCV
- **Screen Capture**: Integration ready for Chrome extension screen capture
- **User Feedback**: Text-based feedback analysis using LLM

### AI Models
- **Vision Transformer (ViT)**: Analyzes images for distraction detection
- **YOLOv11**: Detects user presence and behavioral patterns through pose estimation
- **LLM Integration**: Uses Google Gemini API for feedback analysis and recommendations

### Scoring System
- **Distraction Score**: Measures attention levels (0-100)
- **Presence Score**: Tracks user presence and engagement
- **Behavior Score**: Analyzes posture and activity patterns
- **Overall Score**: Weighted combination of all metrics with letter grades (A-F)

### Notifications
- Real-time alerts for performance drops
- Achievement notifications for good performance
- Customizable notification thresholds
- Session summaries and recommendations

### Data Storage
- MongoDB integration for session data and analytics
- Score trending and historical analysis
- Automatic data cleanup for privacy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AnchorOrg/anchor-insight-AI.git
cd anchor-insight-AI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Install the package:
```bash
pip install -e .
```

## Configuration

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=mongodb://localhost:27017/anchor_insight

# API Keys
GOOGLE_API_KEY=your_google_api_key_here

# Model Settings
VIT_MODEL_NAME=google/vit-base-patch16-224
YOLO_MODEL_PATH=yolov11n.pt

# Thresholds
DISTRACTION_THRESHOLD=0.7
PRESENCE_THRESHOLD=0.8

# Camera
CAMERA_INDEX=0
FRAME_RATE=30
```

## Usage

### Command Line Interface

Start the main application:
```bash
python main.py
```

Start the API server:
```bash
python api.py
```

Or use the console scripts:
```bash
anchor-insight-ai        # Main application
anchor-insight-api       # API server
```

### API Endpoints

The FastAPI server provides the following endpoints:

- `GET /` - Root endpoint
- `GET /status` - Current system status
- `POST /analysis/start` - Start real-time analysis
- `POST /analysis/stop` - Stop analysis
- `POST /feedback` - Submit user feedback
- `GET /scores/recent` - Get recent scores
- `GET /statistics` - Get session statistics
- `GET /trends` - Get score trends
- `GET /notifications` - Get recent notifications
- `POST /notifications/custom` - Send custom notification

### Python API

```python
from main import AnchorInsightAI
import asyncio

async def run_analysis():
    app = AnchorInsightAI()
    await app.initialize()
    await app.start_analysis()

asyncio.run(run_analysis())
```

## Architecture

```
├── main.py                 # Main application entry point
├── api.py                  # FastAPI web server
├── src/
│   ├── config.py          # Configuration management
│   ├── input_processor.py # Camera and input handling
│   ├── ai_models.py       # ViT, YOLO, and LLM integration
│   ├── scoring_system.py  # Score calculation logic
│   ├── notification_system.py # Alert and notification handling
│   └── database.py        # MongoDB integration
├── tests/                 # Unit tests
├── requirements.txt       # Python dependencies
└── setup.py              # Package setup
```

## Models Used

### Vision Transformer (ViT)
- Model: `google/vit-base-patch16-224`
- Purpose: Image classification for distraction detection
- Output: Distraction probability and confidence scores

### YOLOv11
- Model: `yolov11n.pt` (nano version for speed)
- Purpose: Real-time object and pose detection
- Output: Person detection, keypoints, behavioral analysis

### Google Gemini
- API: Google Generative AI
- Purpose: Natural language processing of user feedback
- Output: Sentiment analysis and recommendations

## Database Schema

### Sessions Collection
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "analysis_results": {
    "distraction_analysis": {...},
    "behavior_analysis": {...},
    "feedback_analysis": {...}
  },
  "scores": {...},
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Scores Collection
```json
{
  "session_id": "ObjectId",
  "timestamp": "2024-01-01T12:00:00Z",
  "overall_score": 85.5,
  "individual_scores": {
    "distraction_score": 80.0,
    "presence_score": 90.0,
    "behavior_score": 85.0,
    "feedback_score": 75.0
  },
  "time_metrics": {...},
  "grade": "B",
  "recommendations": [...]
}
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Formatting
```bash
black .
flake8 .
```

### Adding New Models
1. Implement model in `src/ai_models.py`
2. Add configuration options in `src/config.py`
3. Update scoring logic in `src/scoring_system.py`
4. Add tests in `tests/`

## Privacy and Security

- All processing happens locally (except LLM API calls)
- Images are not stored permanently
- Data is converted to numeric/boolean values for storage
- Automatic cleanup of old data
- No personal information is transmitted

## Performance Considerations

- Uses lightweight YOLO nano model for real-time performance
- ViT inference optimized for CPU
- MongoDB indexing for fast queries
- Configurable frame rates and thresholds
- Background processing to avoid UI blocking

## Troubleshooting

### Camera Issues
- Check camera permissions
- Verify camera index in configuration
- Ensure no other applications are using the camera

### Model Loading Issues
- Check internet connection for model downloads
- Verify disk space for model files
- Check Python environment and dependencies

### Database Issues
- Ensure MongoDB is running
- Check connection string in configuration
- Verify database permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

All rights reserved - See LICENSE file for details.
