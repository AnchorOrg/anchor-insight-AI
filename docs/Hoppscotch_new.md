# Anchor Insight AI - Session-Based API Testing with Hoppscotch

## 概述

Hoppscotch 是一个开源的 API 开发环境，用于测试和调试 RESTful API。本文档介绍如何使用 Hoppscotch 测试 Anchor Insight AI 的**会话式专注分析服务**的所有API端点。

> 📌 **重要提示**: 本测试集合基于项目总负责人的最新API需求设计，采用会话模式(Session-based)管理用户的专注监测流程。

## 新架构特点

### 🎯 Session-Based Architecture
- **创建会话**: 用户可以创建专注任务会话，设定目标和时长
- **流处理**: 支持摄像头视频流和屏幕截图的实时上传分析  
- **智能通知**: 基于专注度分析发送提醒和反馈
- **评分报告**: 提供即时评分和完整的会话报告

## 安装和设置

### 1. 安装 Hoppscotch

访问 [Hoppscotch 官网](https://hoppscotch.io) 或下载桌面版:

```bash
# 通过 npm 安装 CLI 版本
npm install -g @hoppscotch/cli

# 或者直接使用 Web 版本
# https://hoppscotch.io
```

### 2. 导入 API 集合

1. 打开 Hoppscotch
2. 点击 **Import/Export** 按钮
3. 选择 **Import from JSON**
4. 上传 `docs/anchor-insight-AI.hoppscotch.json` 文件
5. 确认导入所有请求和环境变量

### 3. 配置环境变量

导入后，检查以下环境变量设置：

**Development Environment:**
- `base_url`: `http://127.0.0.1:7003`  
- `session_id`: `test-session-001`
- `user_id`: `user_123`

**Production Environment:**
- `base_url`: `https://api.anchor-insight.com`
- `session_id`: (需要动态设置)
- `user_id`: (需要动态设置)

## API 端点分组

### 🎯 Session Management (会话管理)

#### 1. Create Focus Session
- **端点**: `POST /api/v1/session`
- **用途**: 创建新的专注会话，设定目标和持续时间
- **测试要点**: 
  - 返回状态码 201
  - 响应包含 session_id, goal, created_at
  - 支持自定义专注类型和优先级

```json
{
  "user_id": "user_123",
  "goal": "Complete code review for project XYZ", 
  "duration_minutes": 60,
  "focus_type": "work",
  "priority": "high"
}
```

### 📹 Stream Processing (流处理)

#### 2. Upload Camera Video Chunk
- **端点**: `POST /api/v1/session/{session_id}/stream/camera`
- **用途**: 上传摄像头视频片段进行人脸检测和专注度分析
- **测试要点**:
  - 支持 multipart/form-data 上传
  - 检测人员是否在镜头前
  - 返回处理状态和时间戳

#### 3. Upload Screen Screenshot
- **端点**: `POST /api/v1/session/{session_id}/stream/screen`
- **用途**: 上传屏幕截图进行应用程序和内容分析
- **测试要点**:
  - 分析屏幕内容的专注相关性
  - 返回专注评分 (0-100)
  - 支持窗口标题上下文信息

### 🔔 Notifications & Feedback (通知与反馈)

#### 4. Send Focus Notification  
- **端点**: `POST /api/v1/session/{session_id}/notifications`
- **用途**: 发送专注提醒和干扰警告
- **测试要点**:
  - 支持多种通知类型 (focus_reminder, distraction_alert等)
  - 基于专注评分触发
  - 返回通知ID和发送状态

#### 5. Submit Session Feedback
- **端点**: `POST /api/v1/session/{session_id}/feedback`  
- **用途**: 提交用户对会话的反馈和评价
- **测试要点**:
  - 收集目标达成情况和用户评分
  - 生成改进建议
  - 返回3条个性化建议

### 📊 Scoring & Reporting (评分与报告)

#### 6. Get Current Session Score
- **端点**: `POST /api/v1/sessions/{session_id}/score`
- **用途**: 获取当前会话的即时专注评分
- **测试要点**:
  - 评分范围 0-100
  - 包含评分细分和等级评定
  - 支持即时计算模式

#### 7. Generate Session Report
- **端点**: `POST /api/v1/sessions/{session_id}/report`
- **用途**: 生成完整的会话分析报告
- **测试要点**:
  - 包含最终评分和等级
  - 提供改进建议数组
  - 生成详细会话摘要

## 测试流程建议

### 1. 基础连通性测试
```bash
# 1. 测试服务状态
GET /health

# 2. 测试根端点
GET /
```

### 2. 完整会话流程测试
```bash
# 1. 创建会话
POST /api/v1/session

# 2. 上传摄像头数据
POST /api/v1/session/{session_id}/stream/camera

# 3. 上传屏幕截图  
POST /api/v1/session/{session_id}/stream/screen

# 4. 发送通知
POST /api/v1/session/{session_id}/notifications

# 5. 获取即时评分
POST /api/v1/sessions/{session_id}/score

# 6. 提交反馈
POST /api/v1/session/{session_id}/feedback

# 7. 生成最终报告
POST /api/v1/sessions/{session_id}/report
```

### 3. 边界情况和错误测试
- **无效会话ID**: 测试不存在的session_id
- **大文件上传**: 测试文件大小限制
- **缺失字段**: 测试必需字段验证
- **格式错误**: 测试无效的请求格式

## 自动化测试脚本

每个请求都包含 JavaScript 测试脚本，自动验证：

- **状态码验证**: 检查HTTP响应代码
- **响应结构验证**: 确认必需字段存在
- **业务逻辑验证**: 验证专注评分范围、数据类型等
- **边界条件测试**: 处理异常情况

### 示例测试脚本
```javascript
// 测试会话创建
pw.test("Session creation returns 201", () => {
  pw.expect(pw.response.status).toBe(201);
});

pw.test("Response has session_id", () => {
  const jsonData = pw.response.json();
  pw.expect(jsonData).toHaveProperty("session_id");
  pw.expect(jsonData).toHaveProperty("goal");
  pw.expect(jsonData).toHaveProperty("created_at");
});
```

## 环境配置

### Development (开发环境)
- **服务器**: `http://127.0.0.1:7003`
- **用途**: 本地开发和调试
- **特点**: 包含详细错误信息，支持热重载

### Production (生产环境) 
- **服务器**: `https://api.anchor-insight.com`
- **用途**: 生产部署测试
- **特点**: 优化性能，简化错误信息

## 注意事项

### 文件上传要求
- **摄像头视频**: 支持 MP4 格式，最大 10MB
- **屏幕截图**: 支持 PNG/JPG 格式，最大 5MB
- **编码要求**: 使用 multipart/form-data

### 会话管理
- **会话ID**: 创建后需要保存用于后续请求
- **超时机制**: 会话24小时后自动过期
- **并发限制**: 每用户最多3个活跃会话

### 错误处理
- **200**: 成功处理
- **201**: 资源创建成功  
- **400**: 请求格式错误
- **404**: 资源不存在
- **413**: 文件过大
- **422**: 验证失败

## 扩展功能

### 批量测试
使用 Hoppscotch CLI 进行批量测试：

```bash
# 运行整个集合
hopp test collection.json

# 运行特定文件夹
hopp test collection.json --folder "Session Management"

# 运行并生成报告
hopp test collection.json --reporter json > test-results.json
```

### CI/CD 集成
将测试集成到持续集成流程：

```yaml
# GitHub Actions 示例
- name: API Testing with Hoppscotch
  run: |
    npm install -g @hoppscotch/cli
    hopp test docs/anchor-insight-AI.hoppscotch.json
```

通过这个全面的测试套件，开发团队可以确保 Anchor Insight AI 的会话式专注分析服务在各种场景下都能正常工作，提供可靠的专注度监测和分析功能。
