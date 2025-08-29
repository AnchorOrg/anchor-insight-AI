# 🚀 开发者环境配置指南

## 📋 快速开始

### 方法1：使用 Pipenv（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd anchor-insight-AI

# 2. 安装 pipenv（如果未安装）
pip install pipenv

# 3. 安装依赖
pipenv install

# 4. 配置环境变量
cp .env.template .env
# 编辑 .env 文件，填入您的配置

# 5. 验证配置
pipenv run python verify_env_config.py

# 6. 启动服务
pipenv shell
python src/main_refactored.py
```

### 方法2：使用 pip

```bash
# 1. 克隆项目
git clone <repository-url>
cd anchor-insight-AI

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.template .env
# 编辑 .env 文件，填入您的配置

# 5. 验证配置
python verify_env_config.py

# 6. 启动服务
python src/main_refactored.py
```

## 🔧 环境变量配置

### 必需配置

1. **OpenAI API Key**
   ```bash
   OPENAI_API_KEY=your-actual-api-key-here
   ```
   - 从 https://platform.openai.com/api-keys 获取
   - 格式：`sk-...` 或 `sk-proj-...`

### 可选配置

2. **开发环境设置**
   ```bash
   ENVIRONMENT=development
   API_RELOAD=true
   LOG_LEVEL=debug
   ```

3. **生产环境设置**
   ```bash
   ENVIRONMENT=production
   API_RELOAD=false
   LOG_LEVEL=info
   ```

## 🧪 验证安装

运行验证脚本：
```bash
python verify_env_config.py
```

该脚本会检查：
- ✅ .env 文件是否存在
- ✅ 所有配置是否正确加载
- ✅ API 密钥格式是否有效
- ✅ 服务启动参数

## 🎯 启动服务

### 开发模式
```bash
# 使用内置服务器
python src/main_refactored.py

# 或使用 uvicorn（支持热重载）
uvicorn src.main_refactored:app --reload --host 0.0.0.0 --port 8001
```

### 生产模式
```bash
uvicorn src.main_refactored:app --host 0.0.0.0 --port 8001 --workers 4
```

## 📚 API 文档

服务启动后访问：
- **API 文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health
- **API 信息**: http://localhost:8001/

## 🛠️ 开发工具

### 运行测试
```bash
# 使用 pipenv
pipenv run pytest

# 使用 pip
python -m pytest
```

### 代码格式化
```bash
# 安装开发依赖
pipenv install --dev

# 格式化代码
black src/
isort src/
```

## 🔍 故障排除

### 常见问题

1. **ImportError: No module named 'src'**
   - 确保在项目根目录运行
   - 检查 PYTHONPATH 设置

2. **OpenAI API Key 错误**
   - 检查 .env 文件中的 API 密钥格式
   - 确认 API 密钥有效且有余额

3. **端口被占用**
   - 修改 .env 文件中的 API_PORT
   - 或使用 `--port` 参数指定其他端口

### 获取帮助

- 查看 [API_Testing_Guide.md](docs/API_Testing_Guide.md)
- 查看 [ARCHITECTURE.md](ARCHITECTURE.md)
- 提交 Issue 到 GitHub

## 📦 依赖说明

### 核心依赖
- **FastAPI**: Web 框架
- **OpenAI**: AI 服务
- **Ultralytics**: YOLO 模型
- **OpenCV**: 计算机视觉
- **Pydantic**: 数据验证

### 开发依赖
- **pytest**: 测试框架
- **black**: 代码格式化
- **isort**: 导入排序
