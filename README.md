# Anchor Insight AI

The application that is taking charge of AI related tasks mainly. 主にAI関連のタスクを担当するアプリケーション

## 🚀 Quick Setup

### Prerequisites
- Python 3.9+ (recommended: Python 3.13)
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

## 🎯 Services

### 1. Main API Gateway (Port 8080)
Central API gateway that coordinates all services
```bash
pipenv run python src/app/main.py
```

### 2. Focus Score Service (Port 8002)
Image analysis service for calculating focus scores
```bash
pipenv run python src/app/get_focus_score.py
```

### 3. Focus Time Service (Port 7003)
Person detection and time tracking service
```bash
pipenv run python src/app/get_focus_time.py
```

### Start All Services
```bash
./entry.sh --start-all
```

### Stop All Services
```bash
./entry.sh --stop-all
```

## 📚 API Documentation

Once services are running:
- **Main API**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health
- **Focus Score API**: http://localhost:8002/docs
- **Focus Time API**: http://localhost:7003/docs

## 🛠️ Additional Commands

```bash
# Show help
./entry.sh --help

# Verify installation only
./entry.sh --verify

# Setup environment file only
./entry.sh --env-only
```

## 📁 Project Structure

```
anchor-insight-AI/
├── entry.sh              # Setup and service management script
├── Pipfile               # Python dependencies
├── .env                  # Environment configuration
├── src/app/
│   ├── main.py          # Main API Gateway
│   ├── get_focus_score.py   # Focus Score Service
│   ├── get_focus_time.py    # Focus Time Service
│   └── give_insight_and_action.py  # Insights Service
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
| `FOCUS_TIME_SERVICE_URL` | Focus time service URL | `http://localhost:7003` |
| `FOCUS_SCORE_SERVICE_URL` | Focus score service URL | `http://localhost:8002` |
| `MAX_FILE_SIZE_MB` | Maximum file size | `10` |
| `URL_TIMEOUT_SECONDS` | Request timeout | `30` |

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
- Ensure all services are running
- Check service URLs in `.env` file
- Verify firewall settings

**OpenAI API errors:**
- Verify your API key in `.env` file
- Check your OpenAI account balance
- Ensure you have access to the specified model

## 📝 License

See [LICENSE](LICENSE) file for details.
