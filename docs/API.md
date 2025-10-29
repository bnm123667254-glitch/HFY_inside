# 📡 API 文档

## 基本信息

- **Base URL**: `http://localhost:8000`
- **API Version**: `v1`
- **API Prefix**: `/api/v1`
- **Content-Type**: `application/json`

## 认证

当前版本暂不需要认证。生产环境请配置 API Key 或 JWT 认证。

## 端点列表

### 1. 健康检查

#### `GET /health`

检查系统健康状态

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "agent": "operational",
    "rag": "operational",
    "vector_store": "operational"
  }
}
```

---

### 2. 系统统计

#### `GET /stats`

获取系统统计信息

**Response**:
```json
{
  "vector_store": {
    "collection_name": "compliance_documents",
    "total_documents": 2156,
    "dimension": 768
  },
  "tools": [
    "knowledge_search",
    "document_summarize",
    "compliance_check",
    "email_draft",
    "report_generate",
    "summary_enhance"
  ],
  "uptime": 3600.5
}
```

---

### 3. 知识问答

#### `POST /api/v1/query`

简单的知识库问答

**Request Body**:
```json
{
  "query": "什么是GDPR？",
  "top_k": 5,
  "include_context": true
}
```

**Parameters**:
- `query` (string, required): 用户问题
- `top_k` (integer, optional): 检索文档数量，默认 5
- `include_context` (boolean, optional): 是否返回检索到的文档，默认 true

**Response**:
```json
{
  "query": "什么是GDPR？",
  "answer": "GDPR（General Data Protection Regulation）即《通用数据保护条例》，是欧盟于2018年5月25日正式实施的数据保护法规...",
  "retrieved_documents": [
    {
      "doc_id": "gdpr_intro_001",
      "content": "GDPR是欧盟最新的数据保护法规...",
      "score": 0.92,
      "metadata": {
        "type": "regulation",
        "region": "EU"
      }
    }
  ],
  "metadata": {
    "document_count": 5,
    "top_score": 0.92
  }
}
```

---

### 4. Agent 任务执行

#### `POST /api/v1/agent/task`

执行复杂的多步任务

**Request Body**:
```json
{
  "task": "搜索关于数据隐私保护的合规文档，生成摘要，并起草一封知会邮件发给团队",
  "context": "我们正在准备隐私政策更新",
  "parameters": {
    "recipient_type": "技术团队"
  },
  "enable_review": true
}
```

**Parameters**:
- `task` (string, required): 任务描述
- `context` (string, optional): 任务上下文
- `parameters` (object, optional): 额外参数
- `enable_review` (boolean, optional): 是否启用审查，默认 true

**Response**:
```json
{
  "task": "搜索关于数据隐私保护的合规文档...",
  "success": true,
  "final_output": {
    "email_draft": "Subject: 数据隐私保护合规更新通知\n\n各位同事：\n\n..."
  },
  "steps": [
    {
      "step_id": 1,
      "description": "搜索数据隐私保护相关文档",
      "tool": "knowledge_search",
      "status": "success",
      "output": {...},
      "error": null,
      "execution_time": 0.45
    },
    {
      "step_id": 2,
      "description": "生成文档摘要",
      "tool": "document_summarize",
      "status": "success",
      "output": {...},
      "error": null,
      "execution_time": 1.23
    },
    {
      "step_id": 3,
      "description": "起草知会邮件",
      "tool": "email_draft",
      "status": "success",
      "output": {...},
      "error": null,
      "execution_time": 0.89
    }
  ],
  "review": {
    "passed": true,
    "quality_score": 0.95,
    "completeness_score": 0.98,
    "issues": [],
    "recommendations": [
      "邮件内容完整，建议添加具体的行动截止日期"
    ],
    "summary": "任务执行成功，所有步骤完成，质量良好"
  },
  "report": "=== AGENT EXECUTION REPORT ===\n...",
  "execution_time": 2.67,
  "metadata": {
    "total_steps": 3,
    "plan_complexity": "medium"
  }
}
```

---

### 5. 文档上传

#### `POST /api/v1/documents/upload`

上传并索引单个文档

**Request Body**:
```json
{
  "doc_id": "privacy_policy_2024",
  "content": "本文档规定了公司数据隐私保护的相关政策...",
  "metadata": {
    "type": "policy",
    "department": "Legal",
    "version": "2.0",
    "effective_date": "2024-01-01"
  }
}
```

**Parameters**:
- `doc_id` (string, required): 文档唯一标识
- `content` (string, required): 文档内容
- `metadata` (object, optional): 文档元数据

**Response**:
```json
{
  "doc_id": "privacy_policy_2024",
  "chunks_indexed": 8,
  "success": true,
  "message": "Successfully indexed 8 chunks"
}
```

---

#### `POST /api/v1/documents/upload/batch`

批量上传文档

**Request Body**:
```json
{
  "documents": [
    {
      "doc_id": "doc_001",
      "content": "...",
      "metadata": {...}
    },
    {
      "doc_id": "doc_002",
      "content": "...",
      "metadata": {...}
    }
  ]
}
```

**Response**:
```json
{
  "total_documents": 2,
  "successful": 2,
  "failed": 0,
  "total_chunks": 15,
  "details": [
    {
      "doc_id": "doc_001",
      "chunks_indexed": 7,
      "success": true,
      "message": "Successfully indexed 7 chunks"
    },
    {
      "doc_id": "doc_002",
      "chunks_indexed": 8,
      "success": true,
      "message": "Successfully indexed 8 chunks"
    }
  ]
}
```

---

### 6. 对话交互

#### `POST /api/v1/chat`

与系统进行多轮对话

**Request Body**:
```json
{
  "message": "告诉我关于GDPR的关键要点",
  "session_id": "user_123_session",
  "use_memory": true
}
```

**Parameters**:
- `message` (string, required): 用户消息
- `session_id` (string, optional): 会话ID，用于保持对话上下文
- `use_memory` (boolean, optional): 是否使用记忆，默认 true

**Response**:
```json
{
  "message": "告诉我关于GDPR的关键要点",
  "response": "GDPR的关键要点包括：\n1. 数据主体权利...\n2. 合法处理基础...\n3. 数据保护官...",
  "session_id": "user_123_session",
  "metadata": {
    "retrieved_documents": 3,
    "response_time": 1.45
  }
}
```

**连续对话示例**:

```bash
# 第一轮
curl -X POST /api/v1/chat -d '{
  "message": "什么是GDPR？",
  "session_id": "session_001"
}'

# 第二轮（继续同一会话）
curl -X POST /api/v1/chat -d '{
  "message": "它的主要要求是什么？",
  "session_id": "session_001"
}'

# 系统会记住之前讨论的是GDPR
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误信息描述"
}
```

### HTTP 状态码

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

### 常见错误

**400 - 缺少必需参数**:
```json
{
  "detail": "Missing 'query' parameter"
}
```

**500 - 执行失败**:
```json
{
  "detail": "Task execution failed: Connection to vector store failed"
}
```

---

## 使用示例

### Python

```python
import requests

# 简单查询
response = requests.post(
    "http://localhost:8000/api/v1/query",
    json={
        "query": "数据加密的最佳实践是什么？",
        "top_k": 5
    }
)

result = response.json()
print(result["answer"])

# Agent 任务
response = requests.post(
    "http://localhost:8000/api/v1/agent/task",
    json={
        "task": "查找ISO 27001相关要求并生成合规检查报告"
    }
)

result = response.json()
print(result["final_output"])
print(result["report"])
```

### cURL

```bash
# 查询
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "GDPR的主要内容", "top_k": 5}'

# Agent 任务
curl -X POST "http://localhost:8000/api/v1/agent/task" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "搜索网络安全相关规定，生成摘要并起草邮件",
    "enable_review": true
  }'

# 上传文档
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "security_policy_001",
    "content": "公司网络安全政策...",
    "metadata": {"type": "policy", "version": "1.0"}
  }'
```

### JavaScript

```javascript
// 查询
const queryResponse = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '什么是数据分类？',
    top_k: 5
  })
});

const queryResult = await queryResponse.json();
console.log(queryResult.answer);

// Agent 任务
const taskResponse = await fetch('http://localhost:8000/api/v1/agent/task', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    task: '查找PCI DSS相关要求并生成合规报告'
  })
});

const taskResult = await taskResponse.json();
console.log(taskResult.final_output);
```

---

## 速率限制

当前版本无速率限制。生产环境建议配置：

- 每 IP 每分钟最多 60 次请求
- Agent 任务每分钟最多 10 次

---

## Webhook (未来支持)

计划支持异步任务的 Webhook 通知：

```json
{
  "webhook_url": "https://your-domain.com/webhook",
  "events": ["task_completed", "task_failed"]
}
```

---

## 版本历史

- **v1.0.0** (2025-10-29): 初始版本
  - 基础查询功能
  - Agent 任务执行
  - 文档管理
  - 对话交互

---

更多信息请访问 [Swagger UI](http://localhost:8000/docs)
