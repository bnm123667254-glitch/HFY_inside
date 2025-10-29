# 🚀 快速开始指南

## 5分钟快速上手

### 前置准备

确保您已安装：
- Python 3.8+
- Docker 和 Docker Compose (用于 Milvus)
- Git

### 步骤 1: 克隆项目

```bash
git clone <repository-url>
cd compliance-qa-agent
```

### 步骤 2: 启动 Milvus

使用 Docker Compose 启动 Milvus 向量数据库：

```bash
docker-compose up -d
```

等待约 30 秒让服务完全启动。检查状态：

```bash
docker-compose ps
```

应该看到 `milvus-standalone`, `milvus-etcd`, 和 `milvus-minio` 都在运行。

### 步骤 3: 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置 API 密钥：

```bash
# 如果使用 Qwen2 (阿里云)
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=your-dashscope-api-key-here

# 或者使用 OpenAI GPT-4
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-openai-api-key-here
```

### 步骤 4: 安装依赖

创建虚拟环境并安装依赖：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 步骤 5: 启动应用

```bash
chmod +x run.sh
./run.sh
```

或直接运行：

```bash
python -m src.api.main
```

应用将在 `http://localhost:8000` 启动。

### 步骤 6: 访问 API 文档

打开浏览器访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 第一个请求

### 1. 上传示例文档

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "gdpr_intro",
    "content": "GDPR（通用数据保护条例）是欧盟的数据保护法规，于2018年5月25日生效。主要保护个人数据和隐私权。",
    "metadata": {
      "type": "regulation",
      "region": "EU"
    }
  }'
```

### 2. 进行查询

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是GDPR？"
  }'
```

### 3. 执行 Agent 任务

```bash
curl -X POST "http://localhost:8000/api/v1/agent/task" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "搜索GDPR相关信息并生成摘要"
  }'
```

## 使用 Python SDK

创建 `test.py` 文件：

```python
import asyncio
from src.models import get_llm
from src.agent import ComplianceAgent
from src.rag import RAGRetriever, MilvusVectorStore
from src.tools.factory import ToolFactory

async def main():
    # 初始化系统
    vector_store = MilvusVectorStore()
    vector_store.connect()

    retriever = RAGRetriever(vector_store)
    llm = get_llm()

    tools = ToolFactory.create_all_tools(llm, retriever)
    agent = ComplianceAgent(llm, tools=tools)

    # 执行任务
    result = await agent.run(
        task="查询数据保护的最佳实践"
    )

    print(result.final_output)

    # 清理
    vector_store.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python test.py
```

## 运行示例

我们提供了完整的示例代码：

```bash
python examples/simple_usage.py
```

这个示例会演示：
1. 系统初始化
2. 文档索引
3. 简单查询
4. Agent 任务执行
5. 复杂多步任务

## 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
pytest tests/ -v
```

## 常见问题

### Q: Milvus 连接失败

**A**: 确保 Milvus 正在运行：

```bash
docker-compose ps
# 如果未运行，启动它：
docker-compose up -d
```

### Q: LLM API 调用失败

**A**: 检查 `.env` 文件中的 API 密钥是否正确配置。

### Q: 向量维度不匹配

**A**: 如果更改了嵌入模型，需要重新创建 Milvus 集合：

```bash
# 停止服务
docker-compose down -v
# 重新启动
docker-compose up -d
```

### Q: 端口被占用

**A**: 修改 `.env` 文件中的端口配置：

```bash
APP_PORT=8001  # 改为其他端口
```

## 下一步

- 📖 阅读完整 [README.md](README.md)
- 🏗️ 了解 [系统架构](docs/ARCHITECTURE.md)
- 📡 查看 [API 文档](docs/API.md)
- 💡 浏览更多 [示例](examples/)

## 获取帮助

- 查看文档目录 `docs/`
- 提交 Issue
- 查看 API 文档 http://localhost:8000/docs

---

祝您使用愉快！
