# Anchor Insight AI - Architecture Documentation

## Overview

This document describes the architecture of the Anchor Insight AI system, which provides real-time focus monitoring and analysis capabilities using computer vision and AI.

## System Architecture

### Layer Architecture

The system follows a clean, layered architecture pattern:

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│        (FastAPI Controllers)           │
├─────────────────────────────────────────┤
│            Service Layer                │
│     (Business Logic Services)          │
├─────────────────────────────────────────┤
│             Model Layer                 │
│        (Data Models & DTOs)            │
├─────────────────────────────────────────┤
│          Configuration Layer           │
│    (Settings & Constants)              │
└─────────────────────────────────────────┘
```

## Inversion of Control (IoC) Implementation

### FastAPI Dependency Injection

The system uses FastAPI's built-in dependency injection system to implement IoC principles:

#### 1. Dependency Providers (`dependencies.py`)
```python
def get_focus_score_settings() -> FocusScoreSettings:
    """Configuration dependency provider"""
    
def get_openai_client(settings: SettingsDep) -> openai.AsyncOpenAI:
    """OpenAI client with lifecycle management"""
    
def get_focus_score_service(client: OpenAIClientDep, settings: SettingsDep) -> FocusScoreService:
    """Service layer dependency provider"""
```

#### 2. Key Benefits
- **Testability**: Easy dependency mocking for unit tests
- **Configuration**: Environment-based configuration injection
- **Lifecycle Management**: Proper resource creation and cleanup
- **Type Safety**: Full type checking for all dependencies
- **Caching**: Automatic dependency caching per request

#### 3. Usage Pattern
```python
@router.post("/analyze/upload")
async def analyze_upload(
    file: UploadFile,
    service: Annotated[FocusScoreService, Depends(get_focus_score_service)]
):
    return await service.analyze_uploaded_file(file)
```

## Module Structure

### Core Modules

1. **`app/`** - Application entry points
   - `get_focus_time.py` - Person monitoring service
   - `get_focus_score.py` - Focus score analysis service

2. **`config/`** - Configuration management
   - `settings.py` - Application settings with environment support
   - Pydantic-based validation and type safety

3. **`controllers/`** - API request handlers
   - `focus_controller.py` - Person monitoring endpoints
   - `focus_score_controller.py` - Focus analysis endpoints
   - Dependency injection for all endpoints

4. **`services/`** - Business logic layer
   - `focus_service.py` - Person monitoring service with session management
   - `focus_score_service.py` - OpenAI integration and image analysis

5. **`models/`** - Data models and DTOs
   - `focus_models.py` - Pydantic models for API requests/responses
   - Type-safe data validation

6. **`constants/`** - Application constants
   - `focus_constants.py` - Centralized constant definitions

7. **`dependencies.py`** - IoC container configuration
   - Dependency provider functions
   - Type aliases for clean injection

## Key Design Patterns

### 1. Dependency Injection Pattern
- **Provider Functions**: Create and configure dependencies
- **Type Annotations**: Ensure type safety across the system
- **Lifecycle Management**: Proper resource allocation and cleanup

### 2. Service Layer Pattern
- **Business Logic Separation**: All business logic in dedicated service classes
- **Single Responsibility**: Each service handles one domain
- **Testability**: Services can be easily unit tested

### 3. Repository Pattern (Configuration)
- **Centralized Configuration**: All settings in one place
- **Environment Support**: Development, testing, production configurations
- **Validation**: Automatic validation of configuration values

### 4. Factory Pattern (Dependencies)
- **Dependency Factories**: Create complex dependencies with proper setup
- **Caching**: Reuse expensive resources within request scope
- **Error Handling**: Centralized error handling for dependency creation

## Service Implementations

### Focus Score Service
- **OpenAI Integration**: Async API calls with retry logic
- **Image Processing**: Base64 encoding and validation
- **Error Handling**: Comprehensive error handling and logging

### Person Monitor Service
- **Session Management**: Multi-user session support
- **Real-time Processing**: Optimized frame processing with threading
- **Time Tracking**: Accurate focus/leave time recording

## Testing Strategy

### Dependency Override
```python
# Test configuration
app.dependency_overrides[get_openai_client] = mock_openai_client
app.dependency_overrides[get_focus_score_settings] = test_settings
```

### Benefits for Testing
- **Isolated Tests**: Each test can have its own dependencies
- **Mock Support**: Easy mocking of external services
- **Configuration**: Test-specific configuration injection

## Performance Considerations

### Resource Management
- **Connection Pooling**: Efficient HTTP client management
- **Memory Usage**: Optimized image processing pipelines
- **Async Operations**: Non-blocking I/O for better throughput

### Caching Strategy
- **Request-level Caching**: Dependencies cached per request
- **Configuration Caching**: Settings cached globally
- **Session Management**: Efficient session state management

## Security Considerations

### API Key Management
- **Environment Variables**: Secure API key storage
- **Validation**: Proper API key format validation
- **Test Mode**: Safe testing without real API keys

### Input Validation
- **File Type Validation**: Strict MIME type checking
- **Size Limits**: Configurable file size restrictions
- **URL Validation**: Secure URL pattern validation

## Deployment Architecture

### Environment Configuration
```
Development:  .env file with test configurations
Production:   Environment variables from deployment system
Testing:      Override dependencies for isolation
```

### Scaling Considerations
- **Stateless Services**: All services are stateless for horizontal scaling
- **Session Management**: External session storage for multi-instance deployment
- **Resource Limits**: Configurable limits for resource usage

## Future Enhancements

### Planned Improvements
1. **Metrics Collection**: Prometheus metrics integration
2. **Distributed Tracing**: OpenTelemetry support
3. **Advanced Caching**: Redis-based caching layer
4. **Database Integration**: Persistent storage for analytics

### Architecture Evolution
- **Microservices**: Split into independent services
- **Event-Driven**: Message queue integration
- **Service Mesh**: Istio for service communication
