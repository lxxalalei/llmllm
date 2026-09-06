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

Phase 0–3 的代码级基础能力已经完成，当前主路线是 Phase 4「规模化知识构建」。项目当前以成熟 Mattermost 代码库的首次存量建库为目标，先建立可复现的业务入口与源码结构基线，再扩展完整 `Channel` 业务域。

当前知识资产：

```text
L1: 12
L2: 4
L3: 4
L4: 11

draft: 18
review: 2
published: 11
```

当前已经具备：

- Go/Python Repository Inventory 与多文件、多 symbol 的 Batch Knowledge Compiler。
- OpenAI Structured Outputs `Code → L1` 生成，以及基于完整 L1 Feature scope 的 `L1 → L2` 综合。
- 由程序校验的 SourceBinding、Markdown/YAML Knowledge Catalog 和递归 lineage。
- 按角色隔离的 Knowledge API、混合检索、grounded QA 和 Knowledge Gap 记录。
- GitHub change intake、changed-symbol 定位、L1/L2 增量重生成、L3 Review routing、L4 过期传播和 Qdrant 增量刷新。
- 显式审批后才写入 canonical Markdown 的发布流程。

下一验收项是以零 LLM 调用生成稳定的 Mattermost API4 路由与 Go symbol 清单、解析失败列表和可复现性报告，为后续 Channel 业务切片建立 Repository Graph 基线。唯一的当前路线和实时状态以 [`docs/roadmap.md`](docs/roadmap.md) 为准。

Phase 3 仍保留一项维护验收债务：尚未用真实上游变化完成 GitHub delivery → regeneration → review/publish → Qdrant 的完整外部链路。

### 运行固定样本 Code → L1

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

仓库 CI 不执行真实模型调用，因为 CI 没有配置 API Key。现有 12 条 L1 继续作为 Channel Creation 的人工基准集；Channel Membership 使用独立人工基准评估批量编译结果。

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
