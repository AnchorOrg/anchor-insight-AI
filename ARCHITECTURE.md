# Layered Architecture Documentation

## 🏗️ Architecture Overview

This project implements a **Layered Architecture** following the **Controller-Service** pattern, promoting separation of concerns and maintainability.

### 📋 Architecture Layers

```
┌─────────────────────────────────────┐
│            Controllers              │  ← HTTP Request/Response handling
├─────────────────────────────────────┤
│             Services                │  ← Business Logic & External API calls
├─────────────────────────────────────┤
│             Models                  │  ← Data structures & validation
├─────────────────────────────────────┤
│             Config                  │  ← Application configuration
└─────────────────────────────────────┘
```

### 🔧 Layer Responsibilities

#### **Controllers** (`src/controllers/`)
- Handle HTTP requests and responses
- Input validation and error handling
- Route requests to appropriate services
- Convert service responses to HTTP responses

#### **Services** (`src/services/`)
- Implement core business logic
- Orchestrate calls to external APIs
- Handle caching and retry logic
- Manage data transformations

#### **Models** (`src/models/`)
- Define data structures using Pydantic
- Input/output validation
- Type safety and documentation
- Request/response schemas

#### **Config** (`src/config/`)
- Application settings and environment variables
- Centralized configuration management
- Type-safe configuration with defaults

## 📁 Project Structure

```
src/
├── controllers/
│   ├── __init__.py
│   └── focus_controller.py        # API request handlers
├── services/
│   ├── __init__.py
│   └── focus_service.py          # Business logic services
├── models/
│   ├── __init__.py
│   └── focus_models.py           # Data models
├── config/
│   ├── __init__.py
│   └── settings.py               # Configuration
├── app/                          # Legacy monolithic files
│   ├── main.py                   # Original monolithic app
│   ├── get_focus_score.py
│   ├── get_focus_time.py
│   └── give_insight_and_action.py
├── main_refactored.py            # New layered architecture app
└── __init__.py
```

## 🚀 Running the Application

### **New Layered Architecture**
```bash
# Start with layered architecture
./entry.sh --start-all-new

# Or manually
pipenv run python src/main_refactored.py
```

### **Legacy Monolithic Architecture**
```bash
# Start with legacy architecture
./entry.sh --start-all

# Or manually
pipenv run python src/app/main.py
```

## 🔄 Service Interactions

### Flow Example: Comprehensive Analysis

```
1. HTTP Request → FocusController.analyze_focus()
2. Controller → FocusAnalysisService.comprehensive_analysis()
3. Service orchestrates:
   - ScreenshotService.capture_screenshot()
   - FocusScoreService.analyze_focus_score()
   - TimeTrackingService.get_time_summary()
   - OpenAIService.generate_management_suggestion()
4. Service → Controller (with processed data)
5. Controller → HTTP Response
```

## 📊 Benefits of This Architecture

### ✅ **Separation of Concerns**
- Each layer has a single responsibility
- Business logic separated from HTTP handling
- Configuration centralized

### ✅ **Testability**
- Services can be tested independently
- Mock external dependencies easily
- Unit tests for each layer

### ✅ **Maintainability**
- Changes to business logic don't affect controllers
- Easy to add new endpoints or services
- Clear code organization

### ✅ **Scalability**
- Services can be extracted to microservices
- Easy to add caching, monitoring, etc.
- Horizontal scaling possibilities

### ✅ **Type Safety**
- Pydantic models ensure data validation
- IDE support with autocompletion
- Runtime type checking

## 🔧 Key Services

### **FocusAnalysisService**
- Main orchestrator for comprehensive analysis
- Manages parallel task execution
- Handles caching and performance optimization

### **HttpService**
- Centralized HTTP client management
- Connection pooling and timeout handling
- Retry logic for external API calls

### **CacheService**
- In-memory caching with TTL
- Performance optimization
- Cache invalidation strategies

### **OpenAIService**
- AI-powered suggestions and insights
- Prompt engineering and response handling
- Error handling for AI service failures

## 🔄 Migration Path

The project supports both architectures:

1. **Current**: Both architectures run side-by-side
2. **Testing**: Use `--start-all-new` to test layered architecture
3. **Migration**: Gradually move functionality to new architecture
4. **Cleanup**: Remove legacy files when confident

## 📝 Development Guidelines

### Adding New Features

1. **Define Models** in `src/models/focus_models.py`
2. **Implement Service Logic** in `src/services/focus_service.py`
3. **Create Controller Methods** in `src/controllers/focus_controller.py`
4. **Add Routes** in `src/main_refactored.py`

### Code Quality Standards

- Use type hints throughout
- Follow Pydantic models for data validation
- Implement proper error handling
- Add logging for debugging
- Write unit tests for services

## 🧪 Testing Strategy

```bash
# Test models
pytest src/test/test_models.py

# Test services  
pytest src/test/test_services.py

# Test controllers
pytest src/test/test_controllers.py

# Integration tests
pytest src/test/test_integration.py
```

## 📈 Performance Considerations

- **Async/Await**: All I/O operations are asynchronous
- **Connection Pooling**: HTTP client reuses connections  
- **Caching**: In-memory cache for frequently accessed data
- **Parallel Processing**: Concurrent task execution
- **Resource Management**: Proper cleanup of resources

This architecture provides a solid foundation for scalable, maintainable, and testable code while preserving the existing functionality.
