# Anchor Insight AI

- The application that is taking charge of AI related tasks mainly. 主にAI関連のタスクを担当するアプリケーション
- A unified FastAPI service that integrates focus analysis and scoring capabilities using modular architecture with dependency injection
- We will try to release another version in the future to make sure that this code repository could be used

## 🏗️ Architecture

This application uses a **unified single-service architecture** (not microservices):
- Single FastAPI application running on port 7003
- Modular controllers and services with dependency injection
- Direct in-process service calls (no HTTP between services)
- Centralized configuration and routing

## 🚀 Quick Setup

### Prerequisites
- Python 3.9+ (recommended: Python 3.12)
- pipenv (will be installed automatically if not present)
- OpenAI API Key

### One-Command Setup
```bash
./entry.sh
```

This will:
- ✅ Check Python version compatibility
- ✅ Install pipenv if needed
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create `.env` file with default configuration
- ✅ Verify installation

### Configuration
After setup, update your `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_actual_api_key_here
```

## 🎯 Running the Application

### Start the Unified Service (Port 7003)
The application runs as a single unified FastAPI service that integrates focus analysis and scoring capabilities.

```bash
pipenv run python src/app/main.py
```

Or using uvicorn directly:
```bash
pipenv run uvicorn src.app.main:app --host 0.0.0.0 --port 7003 --reload
```

## 📚 API Documentation

Once the service is running:
- **API Documentation (Swagger)**: http://localhost:7003/docs
- **API Documentation (ReDoc)**: http://localhost:7003/redoc
- **Health Check**: http://localhost:7003/health
- **Root Endpoint**: http://localhost:7003/

Available endpoints:
- `/api/v1/monitor/*` - Focus time monitoring and person detection
- `/api/v1/analyze/*` - Focus score analysis from images

## 🛠️ Additional Commands

```bash
# Activate virtual environment
pipenv shell

# Run the application
pipenv run python src/app/main.py

# Or using uvicorn with auto-reload for development
pipenv run uvicorn src.app.main:app --host 0.0.0.0 --port 7003 --reload
```

## 📁 Project Structure

```
anchor-insight-AI/
├── entry.sh                      # Setup and dependency installation script
├── Pipfile                       # Python dependencies
├── .env                          # Environment configuration (created from .env.template)
├── src/
│   ├── app/
│   │   └── main.py              # Unified FastAPI application
│   ├── config/
│   │   └── settings.py          # Application settings and configuration
│   ├── controllers/
│   │   ├── focus_controller.py        # Focus monitoring endpoints
│   │   └── focus_score_controller.py  # Focus score analysis endpoints
│   ├── services/
│   │   ├── focus_service.py           # Focus monitoring service
│   │   └── focus_score_service.py     # Focus score analysis service
│   ├── models/
│   │   └── focus_models.py      # Data models and schemas
│   ├── constants/
│   │   └── focus_constants.py   # Application constants
│   ├── dependencies.py           # Dependency injection setup
│   ├── Dockerfile                # Docker container definition
│   └── docker-compose.yml        # Docker orchestration
└── README.md
```

## 🔧 Development

### Virtual Environment
The project uses pipenv for dependency management:
```bash
# Activate virtual environment
pipenv shell

# Install new package
pipenv install package_name

# Install dev dependencies
pipenv install package_name --dev
```

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `MODEL_ID` | OpenAI model to use | `gpt-4o-mini` |
| `MAX_FILE_SIZE_MB` | Maximum file size for uploads | `10` |
| `URL_TIMEOUT_SECONDS` | Request timeout | `30` |
| `API_HOST` | Server host address | `0.0.0.0` |
| `API_PORT` | Server port number | `7003` |
| `API_RELOAD` | Auto-reload on code changes | `false` |
| `LOG_LEVEL` | Logging verbosity | `info` |
| `CAMERA_INDEX` | Camera device index | `0` |
| `CAMERA_WIDTH` | Camera resolution width | `640` |
| `CAMERA_HEIGHT` | Camera resolution height | `480` |
| `CONFIDENCE_THRESHOLD` | YOLO confidence threshold | `0.5` |

## 🚨 Troubleshooting

### Common Issues

**Python version error:**
```bash
# Check Python version
python3 --version
# Ensure you have Python 3.9+
```

**Pipenv not found:**
```bash
# Install pipenv manually
python3 -m pip install --user pipenv
```

**Service connection errors:**
- Ensure the service is running on port 7003
- Check configuration in `.env` file
- Verify firewall settings allow connections to port 7003

**OpenAI API errors:**
- Verify your API key in `.env` file
- Check your OpenAI account balance
- Ensure you have access to the specified model

## 📝 License

See [LICENSE](LICENSE) file for details.
