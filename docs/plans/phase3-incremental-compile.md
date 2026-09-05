# Phase 3 增量知识编译

- 状态：in_progress
- 路线：`docs/roadmap.md` Phase 3
- 样本：Mattermost `Channel Creation`

## 目标

把 Phase 1 已验证的影响分析能力接到真实 Git 变更事件上，并保持 Git/Markdown 为正式知识资产来源。

```text
GitHub push
→ 按 repository + ref 找到已有 L1 SourceBinding
→ 从知识资产绑定 commit 追到 push.after
→ 只读取已有 L1 SourceBinding 覆盖的文件
→ changed symbol
→ repo + commit + file + symbol 精确定位 L1
→ derived_from 反向传播
→ impact report
→ 后续增量重生成 / Review / Publish / Qdrant sync
```

## 当前边界

首个闭环只做“事件读取 + 影响报告”，**不在 Webhook 请求中直接改写正式知识文件**。知识发布仍应经过 Git 产物与 Review，而不是让运行时绕过 canonical store。

当前只对已有 Go SourceBinding 执行 symbol diff；其他语言进入后续扩展。Webhook 的 `before` 用于记录本次 push，但分析基线取自 L1 的 SourceBinding commit；这样即使漏掉一次 delivery，后续 push 也能从知识实际基线补追到最新 `after`。只有与 SourceBinding `ref` 匹配的 branch/tag push 才进入影响分析，feature branch 不会冲击 `master` 知识。

## M1 — Git change intake

- [x] GitHub push API 入口；要求真实 `X-GitHub-Event: push`、40 位 commit SHA 与 Git ref。
- [x] GitHub compare 读取 changed files。
- [x] 按 `repository + ref` 只选择已有 L1 SourceBinding 覆盖的文件。
- [x] 从各文件的 SourceBinding commit 追到 `push.after`；Webhook 漏投时可补追。
- [x] 拉取 baseline/after 源码；空文件与 404 明确区分。
- [x] changed symbol → impact report。
- [x] L1 绑定从 `symbol + commit` 收紧到 `repo + commit + file + symbol`。
- [x] Lineage 角色视图补齐：返回链内每个节点与 SourceBinding 均遵守角色边界。
- [ ] 使用真实可控 GitHub push 做一次外部端到端验证。

## M2 — Incremental regeneration

- 仅对受影响 symbol 调用 Code → L1。
- 对比旧/新 L1，区分 unchanged / changed / removed / added facts。
- 自动更新 L2 草稿。
- L3 变化进入 Review，不自动发布产品真相。

## M3 — Publish and index refresh

- Review 通过后落盘 Markdown/Git。
- 更新 source commit / lineage。
- 只刷新受影响检索资产；必要时保留全量 sync 作为修复工具。
- 验证发布前后普通用户检索结果变化。

## 非目标

- 不修改 Mattermost 上游仓库。
- 不在本阶段接企业 SSO/IAM。
- 不为 Webhook 引入 Kafka、任务集群或复杂事件总线。
- 不让 Qdrant 成为知识真相源。
