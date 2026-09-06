# llmllm

企业产品知识助手：面向已经成熟、功能稳定的大型产品，从现有源码建立可追溯的长期知识资产，并按角色提供不同深度的问答。

## 当前定位

当前主目标不是高频追踪每次代码提交，而是解决：

> 如何把成熟产品已经存在的大量源码，稳定转换成开发、产品、测试和普通员工都能使用的知识。

知识生产与知识消费分离：

```text
Knowledge Build Plane                    Knowledge Serve Plane
成熟产品源码                              用户问题
    ↓                                        ↓
业务域 / Feature Scope                    角色策略
    ↓                                        ↓
L1 Engineering Facts                    检索
    ↓                                        ↓
BehaviorRule                           Grounded Answer
    ├─ L2 Engineering View
    ├─ L3 Product View
    └─ L4 User View
    ↓
Canonical Knowledge / Index
```

## 核心知识模型

### L1 — Engineering Facts

回答“代码实际上做了什么”。保留权限、条件、actor/target、状态变化、错误分支和外部副作用等客观事实。

### BehaviorRule — 结构化业务事实

BehaviorRule 是跨角色视图共用的语义载体，重点保存：

```text
actor
+ action
+ resource
+ conditions
+ decision
+ state_changes
+ side_effects
+ exceptions
+ evidence
```

L2/L3/L4 不再依赖逐层自然语言摘要来传递核心条件，而是从同一条 BehaviorRule 生成不同角色视图。

### L2 — Engineering View

面向开发、测试，描述稳定工程规则。

### L3 — Product View

面向产品、测试、客服，描述产品行为、条件、拒绝规则、状态变化和例外。

### L4 — User View

面向普通员工，形成 FAQ、权限解释、错误原因、操作说明和常见场景知识。

## 源码证据原则

SourceBinding 的职责是可追溯和防止模型伪造来源，不是构建复杂的代码版本追踪系统。

核心证据只要求：

```text
repo + file + symbol
```

`commit/revision`、`start_line/end_line` 仅在代码源能稳定提供时作为辅助定位信息，不作为知识身份、首次建库门禁或全局同步依据。

## 当前阶段

Phase 0–3 的基础能力已经完成，当前主路线是 Phase 4「成熟产品规模化知识构建」。

Mattermost `Channel` 已被拆成一个完整可执行知识域：

```text
Channel
├─ Creation
├─ Membership
├─ Permission
├─ Update / Privacy
└─ Archive / Restore
```

当前分支已经具备：

- Go/Python Repository Inventory 与多文件、多 symbol Batch Compiler；
- OpenAI-compatible Structured Outputs `Code → L1`；
- `L1 → BehaviorRule` 结构化规则生成；
- `BehaviorRule → L2/L3/L4` 三种角色视图投影；
- 五个 Channel Feature scope；
- Channel 域 manifest 与域级覆盖率汇总；
- `scripts/compile_domain.py` 一条命令编译完整 Channel 域；
- 角色隔离的 Knowledge API、Hybrid Retrieval、grounded QA 和 Knowledge Gap；
- GitHub change intake 和增量维护能力，但它们当前是次要维护基础设施。

当前还没有宣称完成的是：在本地 Mattermost checkout + 模型凭据环境中真实跑完五个 Channel Feature，并审核完整的 L1 / BehaviorRule / L2 / L3 / L4 结果。

项目实时路线以 [`docs/roadmap.md`](docs/roadmap.md) 为准。

## 编译完整 Channel 域

配置模型：

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=<支持 Structured Outputs 的模型>
export LLM_API_KEY=<your key>
# 可选：OpenAI-compatible endpoint
export LLM_BASE_URL=<endpoint base url>
```

执行：

```bash
python scripts/compile_domain.py \
  /path/to/mattermost \
  config/knowledge_domains/mattermost-channel.json \
  --output-dir .scratch/channel-domain \
  --summary .scratch/channel-domain-summary.json
```

输出会按 Feature 汇总：

```text
source_files
symbols
l1
behavior_rules
l2
l3
l4
```

生成结果默认是 preview / draft，不因为模型成功生成就自动成为正式知识。

## 存储职责

- Git + Markdown/YAML：正式知识资产和人工可审阅版本历史；
- PostgreSQL：运行数据、关系、状态、查询日志；
- Qdrant：检索索引，不是真相源；
- LangGraph：工作流 orchestration，可替换；
- Tree-sitter：代码结构分析；
- FastAPI：服务接口；
- Pydantic：领域 Schema。

## API

- `GET /health`
- `GET /ready`
- `POST /api/v1/compiler/preview`
- `GET /api/v1/knowledge?role=user|product|test|developer`
- `GET /api/v1/knowledge/{knowledge_id}?role=...`
- `GET /api/v1/knowledge/{knowledge_id}/lineage?role=...`
- `GET /api/v1/knowledge/{knowledge_id}/drill?role=...`
- `POST /api/v1/qa`
- `GET /api/v1/analytics/queries`

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

1. **Mature Product First**：先把成熟产品已有代码变成知识，增量维护不能反过来主导架构。
2. **Knowledge First**：知识资产比 Agent 框架重要。
3. **Code Is Evidence, Not Product Truth**：代码事实不自动等于产品设计。
4. **One Rule, Multiple Views**：L2/L3/L4 从同一 BehaviorRule 投影，而不是连续摘要。
5. **Traceable, Not Over-Defensive**：源码证据做到可追溯即可，不建设不必要的版本防伪链。
6. **Build Once, Serve Many**：知识生产可以重，普通员工查询必须轻。
7. **Role-based Retrieval**：权限在检索层执行，不依赖 Prompt。
8. **Framework Replaceable**：LangGraph、Qdrant、模型均可替换，领域知识模型不能被框架绑死。

## 文档

- [产品需求文档 PRD](docs/PRD.md)
- [系统架构](docs/architecture.md)
- [实施路线图](docs/roadmap.md)
- [当前 Phase 4 实施计划](docs/plans/mattermost-scale-knowledge-bootstrap.md)
- [开发计划约定](docs/plans/README.md)
- [历史计划归档](docs/plans/archive/)
