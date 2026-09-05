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
→ 增量 L1/L2
→ L3 Review
→ Publish 后 Qdrant sync
```

## 当前边界

知识发布仍经过 Git/Markdown 与 Review，不允许 Webhook 或模型运行时绕过 canonical store 直接修改正式知识。当前只对已有 Go SourceBinding 执行 symbol diff；其他语言进入后续扩展。

Webhook 的 `before` 用于记录本次 push，但分析基线取自 L1 的 SourceBinding commit；这样即使漏掉一次 delivery，后续 push 也能从知识实际基线补追到最新 `after`。只有与 SourceBinding `ref` 匹配的 branch/tag push 才进入影响分析，feature branch 不会冲击 `master` 知识。

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

- [x] 仅对已有 SourceBinding 覆盖且发生 `added/modified` 的 symbol 调用 Code → L1；removed symbol 不调用模型。
- [x] 同文件未绑定 symbol 的变化只报告为 `unbound_symbol_changes`，不自动吸收到当前 feature。
- [x] 旧 L1 key/content 作为增量上下文；仍成立的事实要求复用稳定 ID。
- [x] 对比旧/新 L1，区分 unchanged / changed / removed / added；语义变化时升版本。
- [x] 未变化/仅行漂移的 L1 不重新生成，但 SourceBinding 推进到新 commit/file/line。
- [x] 基于更新后的当前 L1 feature scope 重新综合 L2，不允许 Code 直接跳到 L2。
- [x] 对比旧/新 L2；只有 L1 发生语义变化才调用 L2 模型。
- [x] 只有 L2 真正变化才把依赖它的 L3 列入 Review；不自动发布产品真相。
- [x] 同名 Go method、缺失 source symbol、重复 Knowledge ID 等当前 parser 无法安全判定的情况显式失败，不静默丢事实。
- [x] `scripts/regenerate_mattermost_change.py` 提供 Mattermost Channel Creation dry-run：读取知识基线与目标 commit，输出 L1/L2 diff + L3 Review JSON，不写 Markdown/Qdrant。
- [x] dry-run 脚本测试覆盖 tracked file 未变化时无需 LLM，以及 tracked file rename 识别。
- [ ] 使用一次真实 `channel.go` 上游变化执行模型 dry-run。目前 Mattermost master 相对知识基线虽有后续提交，但目标文件尚未变化。

## M3 — Publish and index refresh

- [ ] Review 通过后落盘 Markdown/Git。
- [ ] 更新 source commit / lineage。
- [ ] 只刷新受影响检索资产；必要时保留全量 sync 作为修复工具。
- [ ] 验证发布前后普通用户检索结果变化。

## 验证证据

- PR #4 最新 dry-run/文档收口前一版 CI #81 success；覆盖全部单元/业务测试。
- Copilot 对同名 Go method、静默丢 carried fact、重复 Knowledge ID 的三条 review 均已修复并关闭 thread。
- 当前 Mattermost master 相比知识基线向前推进，但 `server/channels/app/channel.go` 未变化，所以还不能声称完成真实模型增量运行。

## 非目标

- 不修改 Mattermost 上游仓库。
- 不在本阶段接企业 SSO/IAM。
- 不为 Webhook 引入 Kafka、任务集群或复杂事件总线。
- 不让 Qdrant 成为知识真相源。
