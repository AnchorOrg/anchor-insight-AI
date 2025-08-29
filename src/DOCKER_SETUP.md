# Docker Setup Guide for Anchor Insight AI

This guide explains how to use the new Docker-based deployment system for Anchor Insight AI.

## 🐳 Quick Start with Docker

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed ([Get Docker Compose](https://docs.docker.com/compose/install/))

### 🚀 Production Deployment

```bash
# Make the script executable (Linux/macOS)
chmod +x entry.sh

# Start the application in production mode
./entry.sh start

# Or simply run (start is the default)
./entry.sh
```

The application will be available at:
- **API URL**: http://localhost:7003
- **API Documentation**: http://localhost:7003/docs
- **Health Check**: http://localhost:7003/health

### 🔧 Development Mode

For development with live reload:

```bash
./entry.sh dev
```

This will:
- Mount your source code into the container
- Enable automatic restart on code changes
- Use development environment settings

### 📋 Available Commands

| Command | Description |
|---------|-------------|
| `./entry.sh start` | Start in production mode (default) |
| `./entry.sh dev` | Start in development mode with live reload |
| `./entry.sh stop` | Stop the running application |
| `./entry.sh status` | Check application status and health |
| `./entry.sh logs` | View application logs |
| `./entry.sh build` | Build Docker image only |
| `./entry.sh cleanup` | Stop and clean up Docker resources |
| `./entry.sh help` | Show help information |

### 🛠️ Configuration

1. **Environment Variables**: The script automatically creates `.env` from `.env.template` if needed
2. **Customize Settings**: Edit `.env` file to configure OpenAI API keys, camera settings, etc.
3. **Docker Settings**: Modify `docker-compose.yml` for advanced configuration

### 📊 Monitoring

Check application status:
```bash
./entry.sh status
```

View real-time logs:
```bash
./entry.sh logs
```

### 🧹 Cleanup

To stop and clean up all Docker resources:
```bash
./entry.sh cleanup
```

## 🏗️ Docker Architecture

### Files Created
- `Dockerfile`: Multi-stage build for optimized production image
- `docker-compose.yml`: Production deployment configuration
- `docker-compose.dev.yml`: Development overrides
- `.dockerignore`: Optimized build context

### Container Features
- **Multi-stage build**: Smaller production image
- **Non-root user**: Enhanced security
- **Health checks**: Automatic container health monitoring
- **Volume mounts**: Persistent configuration and development workflow

### Ports
- **7003**: Main API service port

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   ./entry.sh stop
   ./entry.sh start
   ```

2. **Environment configuration**:
   - Check `.env` file exists and is properly configured
   - Ensure OpenAI API key is set

3. **Docker permission issues**:
   - Make sure Docker daemon is running
   - Check user permissions for Docker

4. **Build failures**:
   ```bash
   ./entry.sh cleanup
   ./entry.sh build
   ```

For more details, check the logs:
```bash
./entry.sh logs
```
