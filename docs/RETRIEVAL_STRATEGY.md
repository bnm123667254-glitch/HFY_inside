# 三阶段检索策略实现说明

## 当前实现（两阶段）

### 涉及文件：
1. **src/rag/embeddings.py** - 文本嵌入
2. **src/rag/vector_store.py** - 向量检索（粗排）
3. **src/rag/retriever.py** - 阈值过滤和后处理

### 检索流程：
```
用户查询
  ↓
[embeddings.py] 文本 → 向量
  ↓
[vector_store.py] Milvus 向量检索（粗排）
  ↓
[retriever.py] 相似度阈值过滤
  ↓
[retriever.py] 上下文格式化
  ↓
返回结果
```

## 缺失的精排（Reranking）阶段

### 需要添加的功能：

#### 1. 创建 Reranker 模块
**新文件**: `src/rag/reranker.py`

```python
from sentence_transformers import CrossEncoder

class Reranker:
    """二阶段精排模型"""

    def __init__(self):
        # 使用 Cross-Encoder 进行精排
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')

    def rerank(self, query: str, documents: List[RetrievedDocument], top_k: int = 5):
        """
        对粗排结果进行精排

        Args:
            query: 查询文本
            documents: 粗排文档列表
            top_k: 返回top K个文档

        Returns:
            重新排序的文档列表
        """
        # 构建 query-document pairs
        pairs = [(query, doc.content) for doc in documents]

        # Cross-Encoder 重新打分
        scores = self.model.predict(pairs)

        # 按分数排序
        ranked_docs = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [doc for doc, score in ranked_docs[:top_k]]
```

#### 2. 修改 retriever.py
**文件**: `src/rag/retriever.py`

添加精排步骤：

```python
from .reranker import Reranker

class RAGRetriever:
    def __init__(self, vector_store, enable_rerank=True):
        self.vector_store = vector_store
        self.embedding_model = get_embedding_model()
        self.reranker = Reranker() if enable_rerank else None

    def retrieve(self, query: str, top_k: int = 5):
        # 阶段1: 粗排 - 向量检索（召回更多候选）
        initial_k = top_k * 3  # 召回3倍候选
        query_embedding = self.embedding_model.embed_text(query)
        results = self.vector_store.search(query_embedding, top_k=initial_k)

        # 转换为文档对象
        documents = [self._to_document(r) for r in results
                    if r["score"] >= self.similarity_threshold]

        # 阶段2: 精排 - Reranking
        if self.reranker and len(documents) > top_k:
            documents = self.reranker.rerank(query, documents, top_k=top_k)

        # 阶段3: 后处理 - 格式化
        # ... 现有的后处理逻辑

        return documents
```

#### 3. 混合检索（可选增强）
**新文件**: `src/rag/hybrid_search.py`

```python
class HybridRetriever:
    """混合检索：向量检索 + BM25"""

    def __init__(self, vector_store, bm25_index):
        self.vector_retriever = RAGRetriever(vector_store)
        self.bm25_index = bm25_index

    def retrieve(self, query: str, top_k: int = 5):
        # 向量检索
        vector_results = self.vector_retriever.retrieve(query, top_k=20)

        # BM25 检索
        bm25_results = self.bm25_index.search(query, top_k=20)

        # 融合结果（RRF - Reciprocal Rank Fusion）
        merged = self._merge_results(vector_results, bm25_results)

        return merged[:top_k]
```

## 实现优先级

### P0（立即可用）
- ✅ 当前的两阶段检索已经可以满足基本需求
- 检索精度：Top-5 准确率 > 85%（项目文档声明）

### P1（性能优化）
- 添加 Cross-Encoder 精排
- 提升检索精度至 90%+

### P2（高级功能）
- 混合检索（Vector + BM25）
- LLM 重排序
- 多路召回融合

## 性能对比

| 策略 | 召回率 | 精度 | 延迟 | 实现复杂度 |
|------|--------|------|------|-----------|
| 向量检索（当前） | 高 | 中 | 低 | 简单 |
| + Cross-Encoder | 高 | 高 | 中 | 中等 |
| + LLM Rerank | 高 | 很高 | 高 | 复杂 |

## 依赖更新

如果要添加精排，需要在 `requirements.txt` 添加：

```txt
# Reranking
sentence-transformers>=2.2.2  # 已有
# 或使用专门的 reranking 模型
# rank-bm25>=0.2.2  # 如果要BM25
```

---

**总结**：当前系统实现了高效的两阶段检索，足够应对大部分场景。如需进一步提升精度，可按上述方案添加精排阶段。
