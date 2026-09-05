# llmllm

企业产品知识漏斗助手：把源代码持续编译为长期知识资产，并按角色向企业员工提供不同深度的问答。

## 文档

- [产品需求文档 PRD](docs/PRD.md)
- [系统架构](docs/architecture.md)
- [实施路线图](docs/roadmap.md)
- [开发计划约定](docs/plans/README.md)
- [Mattermost Channel Creation 纵向验证（已归档）](docs/plans/archive/mattermost-channel-creation.md)

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

- 12 个真实 L1 Engineering Facts 人工基准（另有 2 轮真实模型 Code→L1 运行预览，未入库）
- 4 个 L2 Engineering Rules 草稿
- 4 个 L3 Product Logic：Mattermost `team_channel` 已 `published`（2026-09-05 产品审核批准），其余处于 `review`；另有 conversation 示例 1 个 `published`
- 11 个 L4 FAQ：Mattermost 10 个（8 published + 2 draft）+ conversation 示例 1 个 published
- Go/Python Tree-sitter symbol parser
- Compiler Preview 可解析实际 Go/Python 源码内容并返回 symbol
- OpenAI Structured Outputs `Code → L1` 生成器
- L1 SourceBinding 由代码侧绑定，模型不能自行声明 repo/ref/file/line
- 本地 Mattermost 固定 commit 生成验证脚本
- Markdown + YAML Knowledge Catalog
- L4 → L3 → L2 → L1 → Code 的递归 lineage
- Knowledge Item / Lineage API

Mattermost 的 L3/L4 当前没有标记为 `published`。代码实现是证据，不自动等于已经确认的产品规则。

### 实际运行 Code → L1

准备一个处于固定 commit 的 Mattermost checkout，并配置：

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=<支持 Structured Outputs 的模型>
export LLM_API_KEY=<your key>
```

使用 OpenAI 兼容端点时（可选）：

```bash
export OPENAI_BASE_URL=<endpoint base url>
```

然后：

```bash
python scripts/generate_mattermost_l1.py /path/to/mattermost --output /tmp/mattermost-l1.json
```

知识检索与问答（Phase 2）：

```bash
export EMBEDDING_MODEL=<embedding model，如 GLM/Embedding-3>
export RETRIEVAL_BACKEND=hybrid   # hybrid | local，默认 hybrid（不可用自动回退 local）
export RERANK=false               # 可选：关闭 LLM rerank（默认开启，增加一次模型调用）
python scripts/sync_qdrant.py     # 将 knowledge/ 资产全量同步到 Qdrant 索引
```

`POST /api/v1/qa` 响应中的 `backend` 字段表示本次实际使用的检索后端。

脚本会拒绝错误 commit、目标源码本地改动、缺失目标 symbol 或缺少模型配置，不会把不匹配的源码标记成固定版本证据。

当前尚未在仓库 CI 中执行真实模型调用，因为 CI 没有配置 API Key。现有 12 条 L1 继续作为真实模型输出的人工基准集。

## API

- `GET /health`
- `GET /ready`
- `POST /api/v1/compiler/preview`
- `GET /api/v1/knowledge?role=user|product|test|developer`：按角色消费边界列出知识（普通用户仅见 Published L3/L4）
- `GET /api/v1/knowledge/{knowledge_id}?role=...`：详情；角色不可见统一返回 404
- `GET /api/v1/knowledge/{knowledge_id}/lineage?role=...`：血缘（可追溯至代码 SourceBinding）
- `GET /api/v1/knowledge/{knowledge_id}/drill?role=...`：向更低知识层下钻（如 L3 → L2）
- `POST /api/v1/qa`：问答助手——按角色检索可见知识资产（混合检索 + LLM rerank），用 LLM 组织 grounded 答案（仅引用实际检索到的知识，`cites` 为资产 id；未覆盖时返回 `knowledge_gap: true`；`backend`/`reranked` 字段说明实际检索后端与是否重排）
- `GET /api/v1/analytics/queries`：查询分析——QA 日志列表与聚合（总量、gap 率、backend 分布、top 命中、最近知识缺口）

`role` 省略时为管理/调试视图，不做过滤。

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
