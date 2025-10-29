# 🏗️ 系统架构设计文档

## 概述

本文档详细描述企业内部智能合规问答与 Agent 助手系统的架构设计、核心组件和技术实现。

## 系统架构

### 整体架构

系统采用分层架构设计，从下至上分为：

1. **基础设施层** (Infrastructure Layer)
2. **数据存储层** (Storage Layer)
3. **核心服务层** (Core Service Layer)
4. **业务逻辑层** (Business Logic Layer)
5. **API 接口层** (API Layer)

```
┌────────────────────────────────────────────────────────────┐
│                      API Layer                             │
│            FastAPI REST API / WebSocket                    │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                      │
│                                                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Agent Framework (P-E-R)                 │   │
│  │                                                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ Planner  │→ │ Executor │→ │ Reviewer │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘       │   │
│  │                                                    │   │
│  │  Features:                                         │   │
│  │  • Task decomposition & planning                   │   │
│  │  • Multi-step execution with tools                 │   │
│  │  • Quality assurance & validation                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Tool Management                       │   │
│  │                                                    │   │
│  │  • Tool Registry & Discovery                       │   │
│  │  • Safe tool invocation                            │   │
│  │  • Input/output validation                         │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│                   Core Service Layer                       │
│                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────┐ │
│  │   RAG System    │  │  Memory Manager │  │   LLM    │ │
│  │                 │  │                 │  │          │ │
│  │  • Retriever    │  │  • Conversation │  │  • Qwen2 │ │
│  │  • Reranker     │  │  • Task State   │  │  • GPT-4 │ │
│  │  • Context      │  │  • Cache        │  │          │ │
│  └─────────────────┘  └─────────────────┘  └──────────┘ │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│                    Storage Layer                           │
│                                                            │
│  ┌─────────────────┐        ┌─────────────────┐          │
│  │  Vector Store   │        │  Session Store  │          │
│  │    (Milvus)     │        │   (In-Memory)   │          │
│  └─────────────────┘        └─────────────────┘          │
└────────────────────────────────────────────────────────────┘
```

## 核心组件详解

### 1. Agent Framework - P-E-R 架构

#### 1.1 Planner (计划器)

**职责**: 任务分解和执行计划生成

**核心功能**:
- 理解用户意图
- 任务分解为可执行步骤
- 生成结构化执行计划
- 依赖关系分析

**技术实现**:
```python
class Planner:
    - LLM: 使用大语言模型进行任务理解
    - JSON Schema: 确保输出结构化
    - Prompt Engineering: 精心设计的规划提示词
    - Validation: 计划合法性验证
```

**输出格式** (TaskPlan):
```json
{
  "task_description": "原始任务描述",
  "steps": [
    {
      "step_id": 1,
      "action": "search",
      "tool": "knowledge_search",
      "parameters": {...},
      "description": "步骤描述",
      "depends_on": []
    }
  ],
  "estimated_complexity": "medium"
}
```

#### 1.2 Executor (执行器)

**职责**: 执行计划中的步骤

**核心功能**:
- 顺序执行步骤
- 工具调用管理
- 中间结果传递
- 错误处理和重试
- 执行状态跟踪

**技术实现**:
```python
class Executor:
    - Tool Registry: 工具注册和查找
    - Execution Context: 执行上下文管理
    - Dependency Resolution: 依赖解析
    - Error Handling: 异常处理机制
```

**执行流程**:
1. 检查步骤依赖是否满足
2. 准备工具输入参数
3. 调用工具执行
4. 记录执行结果
5. 更新执行上下文

#### 1.3 Reviewer (审查器)

**职责**: 执行结果验证和质量保障

**核心功能**:
- 结果完整性检查
- 质量评分
- 问题识别
- 改进建议
- 执行报告生成

**技术实现**:
```python
class Reviewer:
    - LLM-based Review: 基于LLM的智能审查
    - Rule-based Checks: 基于规则的快速检查
    - Quality Metrics: 质量指标计算
    - Report Generation: 详细报告生成
```

**评估维度**:
- Completeness: 完整性 (0-1)
- Quality: 质量 (0-1)
- Correctness: 正确性 (Pass/Fail)

### 2. RAG System (检索增强生成)

#### 2.1 Vector Store (Milvus)

**功能**:
- 高维向量存储
- 高效相似度搜索
- 元数据过滤
- 批量操作

**Schema**:
```python
Collection Schema:
- id: INT64 (Primary Key, Auto-generated)
- doc_id: VARCHAR(256) (Document identifier)
- content: VARCHAR(65535) (Document content)
- embedding: FLOAT_VECTOR(768) (Embedding vector)
- metadata: JSON (Document metadata)

Index: IVF_FLAT (L2 distance)
```

#### 2.2 Embedding Model

**模型**: sentence-transformers/paraphrase-multilingual-mpnet-base-v2

**特性**:
- 多语言支持 (中文/英文)
- 维度: 768
- 语义理解能力强
- 高效推理

#### 2.3 Retriever

**检索流程**:
```
用户查询
    ↓
文本嵌入 (Embedding)
    ↓
向量检索 (Milvus Search)
    ↓
相似度过滤 (Threshold Filtering)
    ↓
上下文格式化 (Context Formatting)
    ↓
返回结果
```

**优化策略**:
- Hybrid Search: 结合语义和关键词
- Reranking: 二次排序提升精度
- Context Window: 智能上下文窗口管理

### 3. Tool System (工具系统)

#### 3.1 Tool Registry

**功能**:
- 工具注册和发现
- 工具元数据管理
- 工具调用路由

**设计模式**: Registry Pattern

#### 3.2 内置工具

| 工具名称 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| knowledge_search | 知识检索 | query, top_k | documents |
| document_summarize | 文档摘要 | documents | summary |
| compliance_check | 合规检查 | scenario | analysis |
| email_draft | 邮件起草 | content, purpose | email_draft |
| report_generate | 报告生成 | content, type | report |
| summary_enhance | 摘要优化 | summary | enhanced_summary |

#### 3.3 Tool 接口规范

```python
class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def invoke(input_data: Dict) -> ToolOutput

    async def ainvoke(input_data: Dict) -> ToolOutput

    def validate_input(input_data: Dict) -> bool
```

### 4. Memory Management (记忆管理)

#### 4.1 Conversation Memory

**功能**:
- 多轮对话上下文保持
- Token 数量控制
- 自动内存修剪
- 历史记录导出/导入

**数据结构**:
```python
@dataclass
class Message:
    role: str  # user/assistant/system
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]

class ConversationMemory:
    messages: List[Message]
    turns: List[ConversationTurn]
    context: Dict[str, Any]
```

#### 4.2 Task Memory

**功能**:
- 任务状态跟踪
- 中间结果存储
- 任务历史记录

### 5. API Layer (API 层)

#### 5.1 主要端点

**Health & Info**:
- `GET /health` - 健康检查
- `GET /stats` - 系统统计

**Query**:
- `POST /api/v1/query` - 简单问答

**Agent**:
- `POST /api/v1/agent/task` - Agent 任务执行

**Documents**:
- `POST /api/v1/documents/upload` - 单文档上传
- `POST /api/v1/documents/upload/batch` - 批量上传

**Chat**:
- `POST /api/v1/chat` - 对话交互

#### 5.2 依赖注入

使用 FastAPI 的依赖注入系统管理组件生命周期:

```python
@lru_cache()
def get_vector_store() -> MilvusVectorStore

def get_retriever() -> RAGRetriever

def get_agent() -> ComplianceAgent
```

## 数据流

### 典型查询流程

```
1. 用户请求
   POST /api/v1/agent/task
   {task: "查找数据安全规定并生成摘要邮件"}

2. Agent Planner 分解任务
   Step 1: knowledge_search(query="数据安全规定")
   Step 2: document_summarize(documents=step_1_output)
   Step 3: email_draft(content=step_2_output)

3. Executor 执行
   3.1 knowledge_search
       → Embedding → Milvus Search → 返回5个文档

   3.2 document_summarize
       → LLM (with context) → 生成摘要

   3.3 email_draft
       → LLM (with template) → 生成邮件

4. Reviewer 审查
   → 评估完整性、质量
   → 生成执行报告

5. 返回结果
   {
     success: true,
     final_output: "邮件草稿...",
     report: "执行报告...",
     steps: [...]
   }
```

## 关键技术决策

### 1. 为什么选择 P-E-R 架构？

- **可解释性**: 清晰的任务分解和执行过程
- **可靠性**: 每个阶段独立验证，降低失败率
- **可扩展性**: 易于添加新工具和功能
- **可维护性**: 关注点分离，便于调试和优化

### 2. 为什么选择 Milvus？

- **性能**: 百万级向量毫秒级检索
- **可扩展性**: 支持分布式部署
- **功能完整**: 支持多种索引和度量
- **社区活跃**: 企业级支持

### 3. 为什么使用 LangChain？

- **生态丰富**: 大量预构建组件
- **抽象良好**: 统一的接口设计
- **快速开发**: 降低开发复杂度
- **社区支持**: 活跃的开发社区

## 性能优化

### 1. 检索优化

- **缓存策略**: 热点查询结果缓存
- **批处理**: 批量嵌入生成
- **索引优化**: IVF 索引参数调优

### 2. LLM 调用优化

- **Prompt 优化**: 精简提示词减少Token
- **并行调用**: 独立任务并行执行
- **流式输出**: 支持流式响应

### 3. 内存管理

- **Token 限制**: 自动修剪超长上下文
- **懒加载**: 按需加载组件
- **连接池**: 数据库连接复用

## 安全考虑

### 1. 输入验证

- Pydantic 模型验证
- SQL 注入防护
- XSS 防护

### 2. 访问控制

- API Key 认证
- Rate Limiting
- IP 白名单

### 3. 数据安全

- 敏感信息脱敏
- 审计日志
- 加密传输

## 监控和运维

### 关键指标

- **性能指标**: QPS, 延迟, 成功率
- **业务指标**: 查询量, 用户活跃度
- **系统指标**: CPU, 内存, 磁盘

### 日志系统

- 结构化日志 (Loguru)
- 日志级别控制
- 日志归档和轮转

## 未来扩展

### 1. 多 Agent 协作

- Agent 间通信协议
- 任务分发和调度
- 结果汇总

### 2. 知识图谱集成

- 实体关系抽取
- 图谱构建
- 图谱检索

### 3. 多模态支持

- 图片文档处理
- PDF 解析
- 表格理解

---

更新日期: 2025-10-29
版本: 1.0.0
