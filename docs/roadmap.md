# Roadmap

本文件是项目路线、状态和下一验收项的唯一索引。产品范围以 [PRD](PRD.md) 为准，架构边界以 [Architecture](architecture.md) 为准，当前实施细节以 [Mattermost 规模的成熟产品存量知识建库](plans/mattermost-scale-knowledge-bootstrap.md) 为准。

路线状态只使用：`pending`、`in_progress`、`blocked`、`completed`、`superseded`。

## 当前路线

- 当前主路线：`Phase 4 — 成熟产品规模化知识构建`
- 路线状态：`in_progress`
- 当前样板：`mattermost/mattermost`
- 当前业务域：完整 `Channel`
- 当前语义链：`Code → L1 → BehaviorRule → L2/L3/L4`
- 当前目标：先建立成熟产品第一版高质量存量知识库，增量维护不是主线。

当前 Channel 域：

```text
Channel
├─ Creation
├─ Membership
├─ Permission
├─ Update / Privacy
└─ Archive / Restore
```

当前已完成：

- BehaviorRule 结构化语义核心；
- `L1 → BehaviorRule` OpenAI-compatible Structured Output extractor；
- `BehaviorRule → L2/L3/L4` 三角色视图；
- BehaviorRule scope pipeline；
- 五个 Channel Feature scope；
- Channel domain manifest；
- `scripts/compile_domain.py` 域级编译入口；
- 域级 coverage 汇总；
- SourceBinding 主证据收口为 `repo + file + symbol`；
- Channel scope 不再依赖固定行号 range；
- CI 已验证新 pipeline 和 Channel domain 配置。

当前未完成：

1. 在真实 Mattermost checkout + 模型凭据环境完整运行五个 Channel Feature；
2. 审核完整 L1 / BehaviorRule / L2/L3/L4 的语义质量；
3. 形成第一版真实 Channel Knowledge Coverage；
4. 发布通过审核的知识到 canonical Markdown / Qdrant；
5. 用代表性真实问题执行 QA 验收；
6. 将 QA Knowledge Gap 转换为下一批知识构建优先级。

### 下一验收项

直接运行完整 Channel 域：

```bash
python scripts/compile_domain.py \
  /path/to/mattermost \
  config/knowledge_domains/mattermost-channel.json \
  --output-dir .scratch/channel-domain \
  --summary .scratch/channel-domain-summary.json
```

验收重点不是“模型有没有成功返回 JSON”，而是：

- L1 是否覆盖真实业务行为；
- BehaviorRule 是否正确保存 actor / condition / allow-deny / state / side effect / exception；
- L2/L3/L4 是否仍表达同一条规则；
- unsupported fact 是否为 0 或被明确剔除；
- 是否可以形成足够回答真实 Channel 问题的知识覆盖。

自动 Repository Graph / 全仓调用图不再是当前步骤的前置条件。只有当手工或半自动 scope 维护成为真实瓶颈时，再增加入口发现自动化。

---

## Phase 0 — Bootstrap (`completed`)

已完成：

- FastAPI；
- Pydantic Knowledge Schema；
- LangGraph workflow skeleton；
- Tree-sitter Python / Go parser；
- PostgreSQL schema；
- Qdrant client；
- Knowledge asset directory；
- tests / CI。

## Phase 1 — 单模块纵向验证 (`completed`)

以 Mattermost `Channel Creation` 为固定样本，验证：

```text
Code
→ L1
→ L2
→ L3
→ L4
→ lineage
→ role view
```

历史目标已完成，相关计划归档于：

- `docs/plans/archive/mattermost-channel-creation.md`

该阶段建立了代码解析、SourceBinding、Knowledge Catalog、lineage、角色消费边界和早期人工知识资产。

## Phase 2 — 检索与问答 (`completed`)

已完成：

- dense embedding；
- local BM25 / sparse；
- Qdrant hybrid retrieval；
- role filter；
- LLM reranker；
- grounded QA；
- query analytics；
- Knowledge Gap；
- Qdrant sync。

历史实施记录：

- `docs/plans/archive/phase2-retrieval-qa.md`

当前原则：问答系统已经足够服务知识构建验证，不继续把检索基础设施当主线。

## Phase 3 — 增量知识维护基础 (`completed`)

已完成：

- GitHub push/change intake；
- changed symbol detection；
- SourceBinding 影响定位；
- L1/L2 增量重生成；
- L3 review routing；
- L4 outdated 传播；
- publish dry-run / approve；
- Qdrant 增量刷新。

历史实施记录：

- `docs/plans/archive/phase3-incremental-compile.md`

当前决策：这些能力保留，但冻结为次要维护基础设施。成熟产品变化少，不再围绕 commit、行号、Webhook 继续扩架构。

## Phase 4 — 成熟产品规模化知识构建 (`in_progress`)

当前实施计划：

- `docs/plans/mattermost-scale-knowledge-bootstrap.md`

### 4.1 已完成：Batch Knowledge Compiler

- Repository Inventory；
- 多文件、多 symbol Feature scope；
- Code → L1；
- preview；
- canonical publish 接口兼容。

### 4.2 已完成：BehaviorRule 语义核心

旧问题：

```text
L1文本
→ L2文本
→ L3文本
→ L4文本
```

会在多轮总结中产生：

- 条件反转；
- actor 扩大/缩小；
- allow/deny 错误；
- 副作用遗漏；
- unsupported ordering。

新链路：

```text
Code
 ↓
L1 Engineering Facts
 ↓
BehaviorRule
 ├─ L2 Engineering View
 ├─ L3 Product View
 └─ L4 User View
```

三种角色视图共享同一结构化规则。

### 4.3 已完成：完整 Channel 域编译结构

Channel 五个 Feature scope 已齐：

```text
Creation
Membership
Permission
Update / Privacy
Archive / Restore
```

域级 manifest：

```text
config/knowledge_domains/mattermost-channel.json
```

域级编译：

```text
scripts/compile_domain.py
```

### 4.4 当前进行：真实 Channel 域知识生成

下一步是真实模型运行与语义审核，而不是继续设计基础框架。

目标产物：

```text
Channel Domain
├─ L1 facts
├─ BehaviorRules
├─ L2 engineering views
├─ L3 product views
├─ L4 user views
└─ coverage summary
```

所有生成内容默认是 `draft`，通过语义审核后才能进入正式知识库。

### 4.5 后续：QA Gap 驱动扩库

Channel 第一版知识发布后，用真实问题测试：

```text
QA
↓
answerable / knowledge_gap
↓
Gap 对应业务域 / Feature
↓
继续补源码范围和知识
```

然后再扩展其他 IM 主域，例如：

- Team；
- User / Account；
- Post / Message；
- Permission / Roles；
- Notification；
- Search；
- File / Attachment；
- Call / Meeting（如果目标产品存在）。

扩展顺序由真实 Knowledge Gap 和业务价值决定，不按代码目录机械推进。

## Phase 5 — 企业化 (`pending`)

在知识生产链被真实验证后，再考虑：

- SSO / IAM；
- Department / Project Permission；
- Review Console；
- Knowledge Coverage UI；
- Evidence Trace UI；
- Monitoring / Cost / Latency；
- 灰度与回滚；
- 企业内部代码平台适配。

## 当前设计决策

### 2026-09-06 — Mature Product First

成熟产品首次存量建库是当前主要矛盾，增量更新降级为次要能力。

### 2026-09-06 — SourceBinding 只承担可追溯

核心证据：

```text
repo + file + symbol
```

commit/revision/line 是可选辅助信息，不参与知识身份和首次建库门禁。

### 2026-09-06 — BehaviorRule 承载跨角色语义

L2/L3/L4 从同一结构化规则生成，不再依赖连续自然语言摘要保存核心业务条件。

### 2026-09-06 — 生成与发布分离

Structured Output 合法或模型成功返回不等于 Published。BehaviorRule pipeline 默认生成 Draft。

### 2026-09-06 — 不把 Repository Graph 当当前前置条件

已有明确 Feature scope 时直接建库。只有 scope 发现成本成为真实瓶颈，才投入入口发现/调用关系自动化。
