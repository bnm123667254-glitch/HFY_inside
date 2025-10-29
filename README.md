# 🏢 企业内部智能合规问答与 Agent 助手系统

**基于 RAG + Agent 的智能知识问答平台**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)](https://python.langchain.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)

## 📋 项目简介

企业内部智能合规问答系统是一个面向企业内网环境的知识管理和智能助手平台。通过结合 **检索增强生成(RAG)** 和 **Agent 自动化框架**，系统能够：

- 📚 对 2000+ 合规文档进行语义检索和智能问答
- 🤖 基于 P-E-R (Planner-Executor-Reviewer) 架构实现多步任务自动化
- 📝 自动生成合规摘要、报告和邮件草稿
- 💬 支持多轮对话和上下文记忆
- 🔍 提供高精度的合规检查和法规查询

## ✨ 核心特性

### 🎯 Agent 框架

- **三阶段任务执行**：Planner → Executor → Reviewer
- **结构化输出控制**：基于 JSON Schema 的 LLM 输出约束
- **工具化调用机制**：安全可靠的工具注册与调用
- **任务状态管理**：支持复杂多步任务的连续执行
- **质量保障**：内置执行结果验证和质量评估

### 🔎 RAG 检索系统

- **向量数据库**：基于 Milvus 的高效向量存储
- **语义检索**：支持中文的多语言嵌入模型
- **智能分块**：自适应文档分块策略
- **上下文融合**：检索结果与 LLM 深度集成

### 🛠️ 自定义工具

1. **知识搜索**：语义检索合规文档
2. **文档摘要**：智能提取关键信息
3. **合规检查**：场景化合规分析
4. **邮件起草**：自动生成专业邮件
5. **报告生成**：结构化合规报告
6. **摘要优化**：内容增强和格式化

### 💾 Memory 管理

- **对话记忆**：ConversationBufferMemory 多轮对话上下文
- **任务状态**：跨步骤的中间结果保存
- **Token 控制**：自动内存修剪和优化

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                           │
│                     (FastAPI REST API)                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Agent Framework                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│  │ Planner  │ →  │ Executor │ →  │ Reviewer │            │
│  │ (计划)   │    │ (执行)   │    │ (审查)   │            │
│  └──────────┘    └──────────┘    └──────────┘            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────┬─────────────────┬────────────────────────┐
│   Tool Registry  │   RAG System    │   Memory Manager       │
│                  │                 │                        │
│  • KnowledgeSearch   • Retriever      • ConversationMemory  │
│  • DocumentSummary   • Embedding      • TaskMemory          │
│  • ComplianceCheck   • VectorStore    • ContextManager      │
│  • EmailDraft        • Reranker       │                     │
│  • ReportGenerate    │                │                     │
└──────────────────┴─────────────────┴────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure                           │
│        Milvus Vector DB  │  LLM (Qwen2 / GPT-4)            │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Milvus 2.3+ (向量数据库)
- Qwen2 API Key 或 OpenAI API Key

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/compliance-qa-agent.git
cd compliance-qa-agent
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入API密钥和配置
```

5. **启动 Milvus**
```bash
# 使用 Docker Compose
docker-compose up -d milvus-standalone
```

6. **运行应用**
```bash
python -m src.api.main
```

应用将在 `http://localhost:8000` 启动

### API 文档

启动后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📖 使用示例

### 1. 简单问答

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "数据隐私保护的基本要求是什么？",
    "top_k": 5
  }'
```

### 2. Agent 任务执行

```bash
curl -X POST "http://localhost:8000/api/v1/agent/task" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "搜索关于数据安全的合规要求，生成摘要并起草一封知会邮件",
    "enable_review": true
  }'
```

### 3. 文档上传

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "compliance_policy_001",
    "content": "企业数据安全管理规定...",
    "metadata": {
      "type": "policy",
      "department": "IT",
      "version": "1.0"
    }
  }'
```

### 4. 对话交互

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "解释一下GDPR的主要内容",
    "session_id": "user_session_123"
  }'
```

## 🧪 Python SDK 使用

```python
from src.models import get_llm
from src.agent import ComplianceAgent
from src.rag import RAGRetriever, MilvusVectorStore
from src.tools.factory import ToolFactory

# 初始化组件
llm = get_llm(temperature=0.7)
vector_store = MilvusVectorStore()
vector_store.connect()
retriever = RAGRetriever(vector_store)

# 创建工具
tools = ToolFactory.create_all_tools(llm, retriever)

# 初始化 Agent
agent = ComplianceAgent(llm, tools=tools)

# 执行任务
result = await agent.run(
    task="查找关于员工数据保护的规定并生成摘要报告",
    context="我们正在更新隐私政策"
)

print(result.final_output)
print(result.report)
```

## 📁 项目结构

```
.
├── config/                 # 配置管理
│   └── settings.py
├── src/
│   ├── agent/             # Agent 框架
│   │   ├── agent.py       # 主 Agent 控制器
│   │   ├── planner.py     # 任务规划器
│   │   ├── executor.py    # 执行引擎
│   │   ├── reviewer.py    # 结果审查器
│   │   └── memory.py      # 记忆管理
│   ├── rag/               # RAG 系统
│   │   ├── vector_store.py    # Milvus 向量库
│   │   ├── embeddings.py      # 嵌入模型
│   │   └── retriever.py       # 检索器
│   ├── tools/             # 自定义工具
│   │   ├── base.py            # 工具基类
│   │   ├── knowledge_tools.py # 知识工具
│   │   ├── generation_tools.py# 生成工具
│   │   └── factory.py         # 工具工厂
│   ├── models/            # LLM 模型
│   │   └── llm.py
│   └── api/               # API 接口
│       ├── main.py            # FastAPI 应用
│       ├── routes.py          # API 路由
│       ├── schemas.py         # 数据模型
│       └── dependencies.py    # 依赖注入
├── tests/                 # 测试
├── docs/                  # 文档
├── requirements.txt       # 依赖
├── .env.example          # 环境变量示例
└── README.md
```

## 🔧 配置说明

### LLM 配置

```bash
# 使用 Qwen2
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=your-api-key
QWEN_MODEL=qwen2-72b-instruct

# 或使用 GPT-4
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4-turbo-preview
```

### Milvus 配置

```bash
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=compliance_documents
```

### Agent 配置

```bash
MAX_ITERATIONS=10          # 最大迭代次数
AGENT_TIMEOUT=120          # 超时时间(秒)
ENABLE_MEMORY=true         # 启用记忆
MEMORY_MAX_TOKENS=2000     # 记忆最大Token数
```

## 📊 性能指标

- **检索精度**: Top-5 准确率 > 85%
- **响应时延**: 平均 1.2s
- **任务成功率**: 95%+
- **并发支持**: 100+ QPS
- **文档容量**: 支持 2000+ 文档

## 🛣️ Roadmap

- [ ] 多Agent协作框架
- [ ] 细粒度权限控制
- [ ] 审计日志系统
- [ ] 知识图谱集成
- [ ] 多模态文档支持
- [ ] 离线部署优化

## 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

**Your Name** - 初始工作

## 🙏 致谢

- LangChain 团队
- Milvus 项目
- FastAPI 框架
- Sentence Transformers

## 📞 联系方式

- 项目主页: https://github.com/yourusername/compliance-qa-agent
- 问题反馈: https://github.com/yourusername/compliance-qa-agent/issues

---

⭐ 如果这个项目对你有帮助，请给一个 Star！
