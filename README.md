# llmllm

企业产品知识漏斗助手：把源代码持续编译为长期知识资产，并按角色向企业员工提供不同深度的问答。

## 文档

- [产品需求文档 PRD](docs/PRD.md)
- [系统架构](docs/architecture.md)
- [实施路线图](docs/roadmap.md)
- [开发计划约定](docs/plans/README.md)
- [Mattermost Channel Creation 纵向验证](docs/plans/mattermost-channel-creation.md)

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

知识生产与知识消费分离：

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
- Tree-sitter：代码结构分析，目前支持 Python / Go
- FastAPI：服务接口
- Pydantic：知识 Schema

## 当前阶段

Phase 1 正在使用 Mattermost 的真实 `Channel Creation` 代码验证完整知识链。

固定样本：

```text
repo: mattermost/mattermost
commit: 43b2ae87e06b06abe01f9382ec26899c54c31728
file: server/channels/app/channel.go
symbols:
  - CreateChannelWithUser
  - CreateChannel
```

当前已经形成：

- 12 个真实 L1 Engineering Facts
- 4 个 L2 Engineering Rules 草稿
- 3 个 L3 Product Logic，状态为 `review`
- 6 个 L4 FAQ 草稿
- Go/Python Tree-sitter symbol parser
- Compiler Preview 可解析实际 Go/Python 源码内容并返回 symbol
- Markdown + YAML Knowledge Catalog
- L4 → L3 → L2 → L1 → Code 的递归 lineage
- Knowledge Item / Lineage API

Mattermost 的 L3/L4 当前没有标记为 `published`。代码实现是证据，不自动等于已经确认的产品规则。

下一主任务不是继续人工扩 FAQ，而是让 `Code → L1` 从当前人工基准事实升级为真实自动生成流程，并用现有 12 条 L1 作为基准集校验生成质量。

## API

- `GET /health`
- `GET /ready`
- `POST /api/v1/compiler/preview`
- `GET /api/v1/knowledge/{knowledge_id}`
- `GET /api/v1/knowledge/{knowledge_id}/lineage`

示例：

```bash
curl http://127.0.0.1:8000/api/v1/knowledge/faq.mattermost.channel.create.limit/lineage
```

## 本地启动

要求：Python 3.12+、Docker / Docker Compose。

```bash
docker compose up -d
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
uvicorn app.main:app --reload
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
