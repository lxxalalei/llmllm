# Roadmap

本文件是项目路线、状态和下一验收项的唯一索引。产品范围以 [PRD](PRD.md) 为准，架构边界以 [Architecture](architecture.md) 为准；[成熟产品存量知识建库](plans/mattermost-scale-knowledge-bootstrap.md) 提供背景，本轮实施入口见下文。历史计划中的状态不能覆盖代码和实际资产。

路线状态只使用：`pending`、`in_progress`、`blocked`、`completed`、`superseded`。

## 当前路线

- 当前主路线：`Phase 4 — 成熟产品规模化知识构建`
- 路线状态：`in_progress`
- 当前样板：`mattermost/mattermost`
- 当前业务域：完整 `Channel`
- 当前目标：把第一版 Channel 基线治理成真正可 QA、可逐 Feature 发布的知识库。
- 最近完成：[Creation L4 用户意图试点](plans/archive/creation-l4-user-intents.md)，已交付规范、草稿入口和离线验收；[使用说明与流程图](l4-user-intents.md)。

当前语义关系：

```text
Code
 ↓
L1 Engineering Facts (N)
 ↓
BehaviorRule (1..N)
 ├─ L2 Engineering View
 └─ L3 Product View

BehaviorRule (N) ↔ L4 User Intent (N)
```

L4 不再是每条 Rule 的机械投影；各层数量不需要相等。

当前 Channel 域：

```text
Channel
├─ Creation
├─ Membership
├─ Permission
├─ Update / Privacy
└─ Archive / Restore
```

### 当前已完成

- BehaviorRule 结构化语义核心；
- `L1 → BehaviorRule` OpenAI-compatible Structured Output extractor；
- BehaviorRule scope pipeline；
- 五个 Channel Feature scope；
- Channel domain manifest 与 `scripts/compile_domain.py`；
- SourceBinding 主证据收口为 `repo + file + symbol`；
- 第一版完整 Channel 主域源码语义核查；
- 第一版 Channel Coverage：20 个核心 L1、20 个初始 BehaviorRule 及对应角色知识；
- 已记录 ABAC membership policy、Join Request、Permanent Delete、Shared Channel remote sync 等明确 Knowledge Gap；
- 已发现并纠正过一次错误的“82 个 review 资产整批 Published”；历史上曾恢复为 `review`。目前部分 Creation、Membership、Permission、Update 资产已 Published，状态以文件为准，不能据此认定真实 QA 已通过；
- 正常 Serve 与 Review 模式分离：正常检索只消费 Published；
- BehaviorRule 自动投影改为 L2/L3，不再强制生成 L4；
- L4 支持 `behavior_rule_ids`，可以组合多个 Rule；
- Membership `add_permission_split` 已从 1 条粗 Rule 拆成 4 条原子 Rule，并由其中 2 条共同支撑 1 条用户 FAQ；
- 已开始清理旧 Creation 正文中的发布日期/审核备注和错误重复知识。
- 已实现独立 L4 意图编写入口：运行时规范、plan/write/review、create/merge/gap、草稿与证据边界；同义问法进入同一知识的 BM25/embedding 输入。Creation 五条参考候选仅保存在 preview，未迁移正式资产。

### 当前未完成

1. 对剩余 Channel BehaviorRule 做原子性审核，确认 Rule 本身包含 L2/L3 所需的关键权限、条件和结果；
2. 完成旧 Creation 与新基线的迁移：真正重复或冲突的资产退出正常 Serve，有独立用户意图价值的 L4 保留；
3. 将代表性 Channel 问题做成真实 QA regression set；
4. 对五个 Feature 执行真实 QA 验收；
5. 按 Feature 逐批 `review → published`，禁止再次整批无 QA 发布；
6. 将 QA Knowledge Gap 转换为下一批知识构建优先级；
7. 需要产品运行环境时再同步 Qdrant，不把数据库接入作为当前知识治理前置条件。

### 下一验收项

Creation 试点已完成 81 项相关测试及离线 15/15 top-4 召回，13 题排名第一。五条参考候选保持草稿，未修改 canonical 资产；真实模型问答执行数为 0，5 道缺口题的拒答仍需验证。证据见 [审阅报告](baselines/creation-l4-review-2026-09-08.md)。

下一轮规划检查点：当前无下一轮计划。候选方向包括真实模型生成与 QA、补齐操作和运行时配置证据、扩展其他 Feature、正式迁移旧知识，待确定范围和优先级再建立有界计划。任何发布仍须先完成真实 QA，不以离线召回或已有 Published 状态替代。

Channel 主路线保留以下验收顺序：

```text
Channel Rule Audit
↓
去掉过粗 Rule / 补齐原子 Rule
↓
User Intent L4 整理
↓
15+ 代表性 QA
↓
逐 Feature Publish
```

验收重点：

- Rule 是否能独立表达 actor / condition / permission / allow-deny / state / side effect / exception；
- L2/L3 是否只依赖 Rule 就能重建核心语义；
- L4 是否围绕真实用户问题，而不是为数量对齐而生成；
- 一个 L4 引用多个 Rule 时，答案是否确实由这些 Rule 共同支撑；
- 正常 Serve 是否完全隔离 Draft/Review/Outdated；
- 同一用户意图是否存在新旧 Published 重复占据 top-k；
- QA 错答是否能回溯到具体 Rule 或缺失源码范围。

自动 Repository Graph / 全仓调用图仍不作为当前步骤的前置条件。

---

## Phase 0 — Bootstrap (`completed`)

已完成：FastAPI、Pydantic Knowledge Schema、LangGraph workflow skeleton、Tree-sitter Python/Go parser、PostgreSQL schema、Qdrant client、Knowledge asset directory、tests/CI。

## Phase 1 — 单模块纵向验证 (`completed`)

以 Mattermost `Channel Creation` 为固定样本，建立了代码解析、SourceBinding、Knowledge Catalog、lineage、角色消费边界和早期人工知识资产。

历史计划：`docs/plans/archive/mattermost-channel-creation.md`。

该阶段使用的连续 `L1 → L2 → L3 → L4` 模型已被当前 BehaviorRule 架构取代，不再作为新知识生产方式。

## Phase 2 — 检索与问答 (`completed`)

已完成 dense embedding、local BM25/sparse、Qdrant hybrid retrieval、role filter、LLM reranker、grounded QA、query analytics、Knowledge Gap、Qdrant sync。

历史记录：`docs/plans/archive/phase2-retrieval-qa.md`。

当前原则：问答基础设施已经足够服务知识质量验证，不继续把检索基础设施当主线。

## Phase 3 — 增量知识维护基础 (`completed`)

已完成 GitHub push/change intake、changed symbol detection、SourceBinding 影响定位、增量重生成、review/outdated 传播、publish 与 Qdrant 增量刷新。

历史记录：`docs/plans/archive/phase3-incremental-compile.md`。

当前决策：这些能力保留，但冻结为次要维护基础设施。成熟产品首次存量建库优先。

## Phase 4 — 成熟产品规模化知识构建 (`in_progress`)

### 4.1 Batch Knowledge Compiler (`completed`)

Repository Inventory、多文件/多 symbol Feature scope、Code → L1、preview、canonical publish 接口兼容。

### 4.2 BehaviorRule 语义核心 (`completed`)

核心原则：

```text
多个 L1 可以支撑一个 Rule
一个 L1 可以拆出多个 Rule
Rule → L2/L3
Rule ↔ L4 为多对多
```

BehaviorRule 必须自己保存核心语义，不能依赖 L2/L3 再从 L1 补回来。

### 4.3 完整 Channel 域结构 (`completed`)

Creation、Membership、Permission、Update/Privacy、Archive/Restore 五个 Feature scope、domain manifest 和域级编译入口已经齐全。

### 4.4 Channel 第一版知识基线 (`completed`)

五个 Feature 已完成第一版真实源码核查、L1/BehaviorRule/L2/L3/L4 基线和 Coverage 报告。

这一步的完成只代表“第一版知识已经存在”，不代表全部可以 Published。

### 4.5 Channel 知识治理与 QA (`in_progress`)

当前工作：

- 撤回未经 QA 的批量发布；
- Rule 原子化；
- L4 用户意图化；
- 新旧 Creation 迁移；
- Serve/Review 隔离；
- QA regression；
- 逐 Feature 发布。

### 4.6 QA Gap 驱动扩库 (`pending`)

Channel 基线通过 QA 后，再根据真实 Knowledge Gap 决定补 Channel 子能力或进入 Team、User/Account、Post/Message、Permission/Roles、Notification、Search、File/Attachment、Call/Meeting 等其他 IM 主域。

## Phase 5 — 企业化 (`pending`)

知识生产链被真实验证后，再考虑 SSO/IAM、部门/项目权限、Review Console、Coverage UI、Evidence Trace UI、监控、灰度、企业内部代码平台适配等。

## 当前设计决策

### 2026-09-06 — Mature Product First
成熟产品首次存量建库是当前主要矛盾，增量更新降级为次要能力。

### 2026-09-06 — SourceBinding 只承担可追溯
核心证据为 `repo + file + symbol`；commit/revision/line 是可选辅助信息。

### 2026-09-06 — BehaviorRule 承载跨角色核心语义
L2/L3 从 Rule 投影，不依赖连续自然语言摘要传递核心条件。

### 2026-09-07 — L4 改为 User Intent Knowledge
L4 不再强制由每个 Rule 一一生成；允许 `Rule 0..N ↔ L4 0..N`。

### 2026-09-07 — Serve 与 Review 分离
正常问答只消费 Published。Draft/Review/Outdated 只有显式 Review 模式才能进入候选。

### 2026-09-07 — QA 前不得批量发布
结构合法和 Semantic Review 均不等于正式发布；必须经过代表性 QA，再按 Feature 发布。

### 2026-09-06 — 不把 Repository Graph 当当前前置条件
只有 scope 发现成本成为真实瓶颈时，才投入入口发现/调用关系自动化。
