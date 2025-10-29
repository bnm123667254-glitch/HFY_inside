"""
Simple Usage Examples
Demonstrates basic usage of the Compliance Q&A system
"""
import asyncio
import sys
sys.path.append('..')

from src.models import get_llm
from src.agent import ComplianceAgent
from src.rag import RAGRetriever, MilvusVectorStore, DocumentProcessor
from src.tools.factory import ToolFactory


async def example_1_setup_system():
    """Example 1: Setup and initialize the system"""
    print("=" * 60)
    print("Example 1: System Setup")
    print("=" * 60)

    # Initialize vector store
    print("\n1. Connecting to Milvus...")
    vector_store = MilvusVectorStore()
    vector_store.connect()
    print("✓ Connected to Milvus")

    # Initialize retriever
    print("\n2. Initializing RAG retriever...")
    retriever = RAGRetriever(vector_store)
    print("✓ RAG retriever ready")

    # Initialize LLM
    print("\n3. Initializing LLM...")
    llm = get_llm(temperature=0.7)
    print("✓ LLM initialized")

    # Create tools
    print("\n4. Creating tools...")
    tools = ToolFactory.create_all_tools(llm, retriever)
    print(f"✓ Created {len(tools)} tools")

    # Initialize agent
    print("\n5. Initializing Agent...")
    agent = ComplianceAgent(llm, tools=tools)
    print("✓ Agent ready")

    return vector_store, retriever, agent


async def example_2_index_documents(vector_store: MilvusVectorStore):
    """Example 2: Index sample documents"""
    print("\n" + "=" * 60)
    print("Example 2: Indexing Documents")
    print("=" * 60)

    processor = DocumentProcessor(vector_store)

    # Sample compliance documents
    documents = [
        {
            "doc_id": "gdpr_overview",
            "content": """
            GDPR（通用数据保护条例）是欧盟于2018年实施的数据保护法规。
            主要要求包括：
            1. 数据主体权利：包括访问权、删除权、数据可携带权
            2. 合法处理基础：需要明确的法律依据
            3. 数据保护官：某些组织必须任命DPO
            4. 数据泄露通知：72小时内向监管机构报告
            5. 隐私设计：将隐私保护融入产品设计
            违反GDPR可能面临高达全球年营业额4%或2000万欧元的罚款。
            """,
            "metadata": {"type": "regulation", "region": "EU", "year": 2018}
        },
        {
            "doc_id": "data_encryption",
            "content": """
            数据加密最佳实践：
            1. 传输加密：使用TLS 1.2或更高版本
            2. 存储加密：敏感数据静态加密，使用AES-256
            3. 密钥管理：使用专业的密钥管理系统(KMS)
            4. 端到端加密：在客户端和服务器之间实现E2EE
            5. 定期更新：定期轮换加密密钥
            6. 备份加密：确保备份数据同样受到加密保护
            加密是数据保护的基础，但不是唯一手段，需配合访问控制、审计等措施。
            """,
            "metadata": {"type": "best_practice", "topic": "encryption"}
        },
        {
            "doc_id": "iso27001_overview",
            "content": """
            ISO 27001 是国际信息安全管理体系标准。
            核心要素：
            1. 信息安全政策：建立组织层面的安全政策
            2. 风险评估：识别和评估信息安全风险
            3. 风险处理：实施控制措施降低风险
            4. ISMS文档：维护完整的管理体系文档
            5. 内部审计：定期审计确保合规
            6. 管理评审：高层定期评审ISMS有效性

            ISO 27001认证可提升组织信息安全管理水平和客户信任。
            """,
            "metadata": {"type": "standard", "standard": "ISO27001"}
        },
    ]

    print("\nIndexing sample documents...")
    for doc in documents:
        chunks = processor.process_document(
            doc_id=doc["doc_id"],
            content=doc["content"],
            metadata=doc["metadata"]
        )
        print(f"✓ Indexed '{doc['doc_id']}' ({chunks} chunks)")

    # Get stats
    stats = vector_store.get_collection_stats()
    print(f"\n✓ Total documents in collection: {stats['total_documents']}")


async def example_3_simple_query(retriever: RAGRetriever):
    """Example 3: Simple knowledge query"""
    print("\n" + "=" * 60)
    print("Example 3: Simple Query")
    print("=" * 60)

    query = "什么是GDPR？"
    print(f"\nQuery: {query}")

    documents = retriever.retrieve(query, top_k=2)

    print(f"\nRetrieved {len(documents)} documents:")
    for i, doc in enumerate(documents, 1):
        print(f"\n[Document {i}] (Score: {doc.score:.3f})")
        print(f"Content: {doc.content[:200]}...")


async def example_4_agent_task(agent: ComplianceAgent):
    """Example 4: Agent multi-step task"""
    print("\n" + "=" * 60)
    print("Example 4: Agent Task Execution")
    print("=" * 60)

    task = "搜索关于数据加密的最佳实践，生成摘要"
    print(f"\nTask: {task}")

    print("\nExecuting task...")
    result = await agent.run(task=task)

    print(f"\n✓ Task completed")
    print(f"  Success: {result.success}")
    print(f"  Steps executed: {len(result.execution_context.results)}")

    print("\n--- Execution Steps ---")
    for step_id, step_result in result.execution_context.results.items():
        print(f"Step {step_id}: {step_result.status.value}")

    print("\n--- Final Output ---")
    if result.final_output:
        output = result.final_output
        if isinstance(output, dict):
            summary = output.get('data', {}).get('summary', 'N/A')
            print(summary[:500])
        else:
            print(str(output)[:500])

    if result.review:
        print("\n--- Review ---")
        print(f"Quality Score: {result.review.quality_score:.2f}")
        print(f"Passed: {result.review.passed}")


async def example_5_complex_task(agent: ComplianceAgent):
    """Example 5: Complex multi-step task"""
    print("\n" + "=" * 60)
    print("Example 5: Complex Multi-Step Task")
    print("=" * 60)

    task = """
    请执行以下任务：
    1. 搜索ISO 27001相关信息
    2. 生成合规摘要
    3. 起草一封介绍ISO 27001的邮件
    """
    print(f"\nTask: {task}")

    print("\nExecuting complex task...")
    result = await agent.run(task=task, enable_review=True)

    print(f"\n✓ Task completed in {sum(r.execution_time for r in result.execution_context.results.values()):.2f}s")

    print("\n--- Execution Report ---")
    print(result.report)


async def main():
    """Main function"""
    try:
        # Example 1: Setup
        vector_store, retriever, agent = await example_1_setup_system()

        # Example 2: Index documents
        await example_2_index_documents(vector_store)

        # Example 3: Simple query
        await example_3_simple_query(retriever)

        # Example 4: Agent task
        await example_4_agent_task(agent)

        # Example 5: Complex task
        await example_5_complex_task(agent)

        # Cleanup
        print("\n" + "=" * 60)
        print("Cleaning up...")
        vector_store.disconnect()
        print("✓ Done")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
