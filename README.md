# llmllm

企业产品知识漏斗助手：把源代码持续编译为长期知识资产，并按角色向企业员工提供不同深度的问答。

## 文档

- [产品需求文档 PRD](docs/PRD.md)
- [系统架构](docs/architecture.md)
- [实施路线图](docs/roadmap.md)

## 核心模型

```text
Source Code
    ↓
L1 Engineering Facts
    ↓
L2 Engineering Rules
    ↓
L3 Product Logic
    ↓
L4 User Knowledge / FAQ
```

知识生产和知识消费分离：

```text
Knowledge Build Plane              Knowledge Serve Plane
Git / Code                         User Query
   ↓                                  ↓
Tree-sitter                        Role Policy
   ↓                                  ↓
LangGraph Compiler                 Retrieval
   ↓                                  ↓
L1 → L2 → L3 → L4                 Answer
   ↓
Git + PostgreSQL + Qdrant
```

- Git + Markdown/YAML：长期知识资产与版本历史
- PostgreSQL：知识元数据、关系、版本、来源绑定
- Qdrant：语义/关键词混合检索索引
- LangGraph：知识生产与更新工作流
- Tree-sitter：代码结构分析
- FastAPI：服务接口
- Pydantic：知识 Schema

## 当前阶段

当前仓库是 V1 bootstrap，目标是先跑通一个真实模块的完整纵向链路：

```text
代码 → L1 → L2 → L3 → L4 → 问答 → 代码变更 → 影响分析 → 增量更新
```

当前已完成：

- FastAPI 应用骨架
- L1-L4 KnowledgeItem 领域模型
- SourceBinding / Relation 基础模型
- LangGraph 知识编译流程骨架
- Python Tree-sitter 解析器
- PostgreSQL 基础表结构
- Qdrant 客户端与健康检查
- 示例 L3/L4 知识资产
- Docker Compose 本地基础设施
- 基础测试与 CI

当前未实现：

- 真实 LLM Provider
- Embedding / BM25 / Hybrid Search
- 代码变更影响分析
- Git Webhook
- 企业 SSO / IAM
- 人工审核后台

这些属于下一阶段，不在 bootstrap 中伪实现。

## 本地启动

要求：Python 3.12+、Docker / Docker Compose。

```bash
docker compose up -d
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

接口：

- `GET /health`
- `GET /ready`
- `GET /api/v1/knowledge/example`
- `POST /api/v1/compiler/preview`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/compiler/preview \
  -H 'Content-Type: application/json' \
  -d '{"source":"conversation/archive_service.py"}'
```

运行测试：

```bash
pytest
```

## 设计原则

1. Knowledge First：知识资产比 Agent 框架重要。
2. Build Once, Serve Many：知识生产可以重，普通员工查询必须轻。
3. Code Is Evidence, Not Product Truth：代码事实不能自动等同于产品设计。
4. Product Logic Is Core：L3 是整个知识体系的关键中间层。
5. Traceable：知识必须能向下追溯来源、向上分析影响。
6. Incremental：代码变化后增量更新，不全库重建。
7. Role-based Retrieval：权限在检索层执行，不依赖 Prompt。
8. Framework Replaceable：LangGraph/Qdrant/模型均可替换，领域模型不能被框架绑死。
