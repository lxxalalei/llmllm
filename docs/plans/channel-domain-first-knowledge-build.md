# Mattermost Channel 全域首次知识建库

- 状态：in_progress
- 路线：[Phase 4 — 成熟产品规模化知识构建](../roadmap.md)
- 所有者：ChatGPT（源码核查、知识生成、语义验收）
- 分支：`codex/channel-domain-knowledge`

## 目标

在不依赖 PostgreSQL、Qdrant 或外部模型 API 的前提下，直接读取真实 Mattermost Channel 域源码，完成第一版可审核的 Channel 知识基线。

目标链路：

```text
Mattermost source
→ L1 Engineering Facts
→ BehaviorRule
→ L2 Engineering View / L3 Product View / L4 User View
→ Semantic Review
→ Canonical Markdown
→ Channel Knowledge Coverage
```

## 范围

本轮只覆盖完整 Channel 主域五个 Feature：

1. Channel Creation
2. Channel Membership
3. Channel Permission
4. Channel Update / Privacy
5. Channel Archive / Restore

源码范围以 `config/knowledge_scopes/mattermost-channel-*.json` 为初始入口；若关键业务条件依赖 scope 外 helper，只沿真实调用补充必要证据，不展开全仓调用图。

## 知识原则

- SourceBinding 核心只使用 `repo + file + symbol`；commit/line 不是知识身份。
- L1 只写源码能直接支持的事实，不推断产品意图。
- BehaviorRule 只承载会影响业务行为的 actor/action/conditions/decision/state changes/side effects/exceptions。
- L2/L3/L4 从同一业务事实生成，不允许逐层摘要改变条件范围。
- 不因为生成成功自动发布；本轮先形成经过人工语义核查的基线资产。
- 不为了“覆盖率好看”制造重复知识。

## 执行步骤

### M1 — Source Review

逐个 Feature 阅读 scope 中真实 symbol，并补查影响权限、拒绝条件、状态变化、副作用的 helper。

验收：每个最终规则至少有一个明确的真实源码 symbol 支撑。

### M2 — L1 + BehaviorRule

从源码形成去重后的 L1，并整理 BehaviorRule。

重点检查：

- self / other；
- actor / target；
- public / private / space / direct / group 类型边界；
- allow / deny；
- permission / policy / feature flag；
- state write / delete；
- WebSocket / system post / plugin lifecycle；
- 特殊 bypass / exception。

### M3 — Role Views

从规则直接形成 L2、L3、L4。

验收：三种角色视图不得新增源码未支持的条件或结论。

### M4 — Semantic Review

对每个 Feature 做语义验收：

- 条件没有反转；
- actor 范围没有扩大或缩小；
- allow/deny 正确；
- 关键状态变化和副作用没有明显遗漏；
- 重复规则合并；
- unsupported ordering 删除或降级为不声明顺序。

### M5 — Canonical + Coverage

把通过审核的知识落到 `knowledge/`，并输出 Channel Coverage 报告，明确：

- 各 Feature 已覆盖的业务主题；
- L1 / BehaviorRule / L2 / L3 / L4 数量；
- 已知缺口；
- 后续 QA 应验证的问题集合。

## 非目标

本轮不做：

- PostgreSQL 写入；
- Qdrant 同步；
- Embedding / Rerank；
- Webhook / commit change tracking；
- Repository Graph；
- Mattermost 全量测试；
- 自动发布全部生成结果。

## 完成标准

本计划完成时必须同时满足：

1. 五个 Channel Feature 都有真实源码审核记录；
2. 每个 Feature 都形成 L1 + BehaviorRule + L2/L3/L4；
3. 经过一次明确的 Semantic Review；
4. 通过审核的资产已经落入 canonical `knowledge/`；
5. 有一份 Channel Knowledge Coverage 报告；
6. 项目测试/CI 不因新增知识资产失败。
