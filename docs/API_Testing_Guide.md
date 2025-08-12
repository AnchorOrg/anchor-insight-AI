# Anchor Insight AI - API Testing Guide

## 🚀 Hoppscotch测试集合使用指南

本文档介绍如何使用Hoppscotch测试集合来全面测试Anchor Insight AI的统一API服务。

### 📦 安装Hoppscotch

```bash
# Windows用户使用winget安装
winget install --id=hoppscotch.Hoppscotch -e

# 或者直接访问Web版本
# https://hoppscotch.io/
```

### 📁 测试集合结构

我们的测试集合包含以下几个主要部分：

#### 🏠 Core Endpoints（核心端点）
- **Root Service Info** - 获取服务基本信息
- **Health Check Global** - 全局健康检查

#### 📹 Focus Monitor（摄像头焦点监控）
- **Monitor Health Check** - 监控服务健康检查
- **Start Monitoring Session** - 开始监控会话
- **Get Monitor Status** - 获取监控状态
- **Get Focus Score** - 获取焦点分数
- **Get Time Records** - 获取时间记录
- **Get Session Summary** - 获取会话总结
- **Get Latest Record** - 获取最新记录
- **Stop Monitoring Session** - 停止监控会话
- **List All Sessions** - 列出所有会话
- **Delete Session** - 删除会话

#### 🖼️ Focus Analysis（图像焦点分析）
- **Analyze Health Check** - 分析服务健康检查
- **Detailed Health Check** - 详细健康检查
- **Upload Image for Analysis** - 上传图像进行分析

#### 🧪 Edge Cases & Error Testing（边界情况和错误测试）
- **Invalid Endpoint 404 Test** - 测试不存在的端点
- **Invalid Session ID Test** - 测试无效会话ID
- **Malformed JSON Test** - 测试格式错误的JSON

### 🔧 使用步骤

#### 1. 启动服务
```bash
cd anchor-insight-AI
export PYTHONPATH="$(pwd)"
export OPENAI_API_KEY="your-openai-api-key"
export ENVIRONMENT="development"
python -m uvicorn src.main_refactored:app --host 127.0.0.1 --port 8003
```

#### 2. 导入测试集合
1. 打开Hoppscotch应用
2. 点击"Import/Export"
3. 选择"Import from JSON"
4. 导入 `docs/anchor-insight-AI.hoppscotch.json` 文件

#### 3. 运行测试

**基础测试流程：**
1. 先运行 `🏠 Core Endpoints` 验证服务正常
2. 运行 `📹 Focus Monitor` 按顺序测试监控功能
3. 运行 `🖼️ Focus Analysis` 测试图像分析功能
4. 运行 `🧪 Edge Cases` 测试错误处理

### 📝 测试脚本说明

每个请求都包含了自动化测试脚本，验证：

- **状态码正确性** - 确保返回预期的HTTP状态码
- **响应结构** - 验证响应JSON的必需字段
- **业务逻辑** - 检查返回数据的合理性

### ⚠️ 重要的边界测试用例

#### 监控服务边界测试：
1. **重复启动会话** - 测试多次启动同一会话的处理
2. **停止不存在的会话** - 测试停止不存在会话的错误处理
3. **无效会话ID查询** - 测试使用不存在的会话ID查询状态
4. **并发会话管理** - 测试多个会话同时运行的情况

#### 图像分析边界测试：
1. **无文件上传** - 应该返回422 Unprocessable Entity
2. **错误文件类型** - 上传非图像文件应该返回400 Bad Request
3. **文件过大** - 超出限制的文件应该返回413 Payload Too Large
4. **损坏的图像文件** - 应该优雅处理并返回适当错误

#### 系统级边界测试：
1. **高频率请求** - 测试API的并发处理能力
2. **长时间运行会话** - 测试内存泄漏和资源管理
3. **服务重启恢复** - 测试服务重启后会话状态的处理

### 🎯 预期测试结果

#### 成功响应示例：

**健康检查 (200 OK):**
```json
{
  "status": "healthy",
  "api_version": "1.0.0"
}
```

**监控状态 (200 OK):**
```json
{
  "is_monitoring": true,
  "person_detected": false,
  "session_id": "test-session-001",
  "uptime": 123.45
}
```

**焦点分析 (200 OK):**
```json
{
  "focus_score": 85,
  "confidence": "high",
  "analysis": "Person appears focused",
  "timestamp": "2025-08-11T17:30:00Z"
}
```

#### 错误响应示例：

**未找到端点 (404):**
```json
{
  "detail": "Not Found"
}
```

**无效请求 (422):**
```json
{
  "detail": [
    {
      "loc": ["body"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 🔄 持续集成建议

建议将这些测试集成到CI/CD流程中：

1. **预部署测试** - 在每次部署前运行完整测试套件
2. **健康监控** - 定期运行健康检查端点
3. **回归测试** - 在功能更新后运行相关测试用例
4. **性能基线** - 记录响应时间作为性能基线

### 📚 故障排除

#### 常见问题：

**连接被拒绝：**
- 确保服务正在运行在正确端口（8003）
- 检查防火墙设置
- 验证服务启动日志

**OpenAI API错误：**
- 确保设置了有效的OPENAI_API_KEY
- 检查API配额和权限
- 验证网络连接

**文件上传失败：**
- 确保图像文件格式正确（JPEG, PNG等）
- 检查文件大小限制
- 验证Content-Type头设置

---

## 🎉 开始测试

现在你可以使用这个完整的测试集合来验证Anchor Insight AI服务的所有功能！

记住：好的测试不仅验证正常情况，更重要的是验证边界情况和错误处理。
