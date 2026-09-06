# Knowledge Expansion — 规模化知识构建

- 状态：superseded
- 路线：[Phase 4 — 规模化知识构建](../../roadmap.md#phase-4--规模化知识构建-in_progress)
- 替代计划：[Mattermost 规模的成熟产品存量知识建库](../mattermost-scale-knowledge-bootstrap.md)
- 替代原因：项目从单个 Batch Scope 的语义修复，调整为面向成熟产品首次存量建库的业务入口发现、Business Scope 和 BehaviorRule 主链路。
- 当前样本：Mattermost `Channel`
- 目标：从“单个 Feature 验证”扩展到“完整业务模块持续编译”，优先扩大知识覆盖率，再继续深化增量维护能力。

## 为什么切换主线

Phase 3 已具备 Git change intake、增量 L1/L2、L3 Review routing、Publish 与 Qdrant 增量刷新基础能力。当前主要短板不是“知识变化后如何传递”，而是正式知识库覆盖范围仍然很小。

当前主线因此调整为：

```text
已有产品代码
→ Repository Inventory
→ Feature Scope
→ Batch Knowledge Compiler
→ L1 Engineering Facts
→ L2 Engineering Rules
→ Review / Publish
→ Qdrant
→ QA
→ Knowledge Gap
→ 下一批知识构建
```

增量更新能力保留为 Maintenance Infrastructure，本阶段不继续扩展 Webhook、队列或自动发布架构。

## M1 — Repository Inventory

目标：回答“仓库里有什么值得进一步划分为知识编译范围的代码”。

- [x] 支持 Go / Python 源文件扫描。
- [x] 输出文件、语言、top-level symbol、行范围。
- [x] 支持只扫描指定文件或目录，不要求全仓库扫描。
- [x] 跳过常见依赖/构建目录，不扫描 Markdown 等非支持源码。
- [x] CLI：`scripts/inventory_repository.py`。

Inventory 只陈述代码结构，不自动把文件名猜成产品 Feature。

## M2 — Batch Knowledge Compiler

目标：一个 Feature 可以由多个文件、多个 symbol 共同组成，不再把“一个函数”当成完整产品功能。

- [x] JSON Scope 描述 `repo/ref/namespace/module/feature/sources/symbols`。
- [x] 每个 source 独立解析并生成 L1，SourceBinding 保留真实 file/symbol/line。
- [x] 多文件 L1 汇总后统一综合 L2。
- [x] 跨文件重复 Knowledge ID 显式失败，不静默覆盖。
- [x] target symbol 缺失显式失败。
- [x] preview 输出兼容现有 Publish：`l1_changes/l1_items/l2_changes/l2_items/l3_review`。
- [x] CLI：`scripts/compile_scope.py`。
- [x] 首个真实 scope：`config/knowledge_scopes/mattermost-channel-membership.json`。

第一版只用于“新 Feature 首次建库”。已经存在 L1/L2 的 Feature 继续走既有增量 regeneration，避免初始编译和维护逻辑混在一起。

## M3 — Channel 模块扩展

按业务 Feature 而不是按代码文件扩展：

1. Channel Membership
2. Channel Permission
3. Channel Update
4. Channel Archive / Restore
5. Channel Creation（已有基线，用于对照）

Channel Membership 已先完成一轮人工源码追踪，基准见 [`docs/baselines/mattermost-channel-membership.md`](../../baselines/mattermost-channel-membership.md)。人工基准不直接写入 canonical knowledge，它用于检查真实 Batch Compiler 输出是否覆盖关键事实、是否出现 unsupported fact / duplicate / wrong binding。

当前 Channel Membership scope 已从最初的 API + `channel.go` 入口扩展到 guard、discoverable self-add 和成员变更 system-post 辅助函数；join request、shared-channel/syncables 仍作为相邻调用路径，不无限扩大单个 Feature 的输入边界。

每个 Feature 的验收不是“模型跑完”，而是：

- Source scope 可解释；
- L1 事实有代码证据；
- L2 规则无明显重复/错误抽象；
- Publish 后可检索；
- 用真实问题验证问答覆盖。

真实运行与人工审核已于 2026-09-06 完成，详见 [`docs/baselines/mattermost-channel-membership-review-2026-09-06.md`](../../baselines/mattermost-channel-membership-review-2026-09-06.md)。编译链路和结构校验通过，输出 67 L1 / 19 L2；但 L1 粒度偏细、L2 抽象不足，本轮不发布。

收紧迭代已完成：新增 route-level 可控 source range、L1 symbol 分块与完整性/数量门禁、L2 最多 10 条门禁；DeepSeek Pro v4 输出 49 L1 / 10 L2，所有结构门禁通过。语义复核仍发现 unsupported ordering 与高价值 L2 主题遗漏，本轮仍不发布。

归档时未完成项：增加基于 source / `derived_from` 的语义 Review/Repair 阶段和基线主题 coverage gate。该目标已并入替代计划的 M3，不再作为当前路线入口。

2026-09-06 决策：Mattermost 是开源样板，不要求用户承担产品审核。Batch scope 新增 `propagation: auto_publish`，允许通过技术门禁的 L2 自动生成 Published L3/L4；默认仍是 `review`，不影响未来自有产品。首次完整运行产出 50 L1 / 9 L2 / 9 L3 / 16 L4，但自动技术复核仍发现权限范围收缩和 FAQ 条件反转，因此本次未写入 canonical knowledge。

## M4 — Coverage + Knowledge Gap

后续增加 Knowledge Coverage Report：

```text
发现 Feature 数
已编译 Feature 数
L1 / L2 / L3 / L4 数量
已发布数量
QA 已验证 Feature 数
Knowledge Gap 数
```

再把现有 `knowledge_gap=true` 接回知识生产入口，让真实问题决定下一批优先补什么知识。

## 当前非目标

- 不继续扩 Webhook / change propagation 复杂度。
- 不引入 Kafka、任务集群或复杂扫描框架。
- 不把“分析了多少函数”当成知识覆盖率。
- 不让模型仅根据文件名自动决定产品逻辑。
- 不在批量 Code → L1/L2 尚未稳定前自动生成并发布 L3/L4。
