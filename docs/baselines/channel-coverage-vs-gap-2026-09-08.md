# Mattermost Channel 覆盖能力 vs 已知缺口对照 — 2026-09-08

目的：给出每个 Channel Feature 当前“已覆盖能力 / 已登记缺口”的可核对清单，作为 4.5 治理 QA 与 4.6 Gap 驱动扩库的输入。本文件只汇总事实，不改变任何资产状态。

## 事实来源

- 落库原子规则：`knowledge/behavior-rules/mattermost/channel-*/**`（39 条 YAML 文件名即规则名）。
- canonical 资产状态：`knowledge/{l1-engineering-facts,l2-engineering-rules,l3-product-logic,l4-user-knowledge}/mattermost/**`（frontmatter status）。
- 基线：`docs/baselines/mattermost-channel-domain-knowledge-2026-09-07.md`、`mattermost-channel-governance-review-2026-09-07.md`、`legacy-creation-migration-audit-2026-09-08.md`。
- QA 题目集：`config/qa_regression/channel-2026-09-08.json`（18 题）。

## 术语

- “已覆盖”= 有真实源码证据、已落库原子 BehaviorRule / 对应角色资产。
- “已知缺口”= 基线审计或 QA 题目中明确登记、尚未结构化的能力。
- “published”= 状态已翻转，正常 Serve 可见；不等于已通过当前 18 题 QA 验收。

## 总览对照

| Feature | 原子 Rule | canonical 发布状态 | 已覆盖能力核心 | 已知缺口 |
|---|---|---|---|---|
| Creation | 8 | 治理基线大多 draft/review；serve 面仍为 legacy published | Open/Private 创建权限、类型边界、可发现私有门禁、创建者自动入会、副作用链 | 治理资产未 QA/发布；“频道数量上限”暂无治理 L4 意图；6 条 legacy 重叠待退役（待产品决策） |
| Membership | 11 | 全部 published（L1 5 / L2 11 / L3 11 / L4 5） | self-add vs add-other、类型边界、group 约束、guarded hook、加/移生命周期与清理、Town Square 保护 | Join Request 完整生命周期；ABAC membership policy 调用路径未核清；Shared Channel remote sync |
| Permission | 3 | 全部 published（L1 3 / L2 3 / L3 3 / L4 3） | manage_member_roles、base scheme 身份保持、moderation 上限、bulk import 例外 | 成员级偏好（notification props / autotranslation）未进基线 |
| Update / Privacy | 9 | 全部 published（L1 4 / L2 9 / L3 9 / L4 4） | 属性权限按类型拆、DM/GM 受限更新、隐私转换方向拆分、guarded hook、discoverable 门禁 | AutoTranslation / Managed Category 专用字段路径未做 Rule |
| Archive / Restore | 8 | 全部 review（未发布）：L1 4 / L2 8 / L3 8 / L4 4 | 归档/恢复权限、Town Square 保护、软删除、guarded hook、事件与状态恢复 | Permanent Delete 深度清理；Shared Channel 远端同步；API 归档 audit 即时性（QA g2 预期 Gap） |

## Membership 详细对照（样例 Feature）

### 已覆盖原子规则（11 条）

| 规则 | 已覆盖业务能力 |
|---|---|
| `open-self-add-permission` / `open-add-other-permission` | 公开频道自助加入 vs 代加他人权限差异；FAQ“为什么能自己加、不能加别人”由两条共同支撑 |
| `private-add-permission` | 私有频道成员管理权限 |
| `direct-group-add-rejected` | Direct/Group 普通加人入口拒绝 |
| `discoverable-self-add` | 可发现私有频道 direct self-add 复合门禁（必须走申请入口） |
| `team-member-integrity` | 目标必须是团队成员 + 显式内部 bypass |
| `member-add-type-boundary` | Open/Private/Space 类型边界 |
| `group-constrained-membership` | 群组约束频道只允许群组成员 |
| `member-add-guarded-hook` | `runGuardedChannelMemberWillBeAdded` 拒绝语义 |
| `add-lifecycle` / `remove-cleanup` | 加入的 join history/system post/双路事件；移除的 ChannelMember+ThreadMembership 清理、leave history、双路 `user_removed` |
| Town Square 保护 | 非 Guest 不可移除（随 remove-cleanup 及 L3/L4 表达） |

### 已知缺口（基线原文，2026-09-07）

1. **ABAC membership policy 细节**：`channel_join_request.go` 注释声称 `AddChannelMember/addUserToChannel` 会再次执行 PDP，但主 `channel.go` 核查未找到同名显式 `evaluateChannelMembership` 调用——暂不把注释升级为 BehaviorRule，需单独核清真实调用路径。
2. **Join Request 完整生命周期**：仅覆盖入口规则；request / withdraw / approve / deny / reviewer queue 未结构化。
3. **Shared Channel remote sync**：成员操作的远端集群同步副作用未完整结构化。

## Creation 待产品决策（来自 legacy 迁移审计 2026-09-08）

1. “频道数量上限”是否补为治理 Creation 的新 L4 意图（推荐：是）。
2. legacy 与治理同意图重叠的 6 条资产，随治理发布置 `deprecated`（可追溯）还是直接删除。

## 结论

- 无任何 Feature 带“遍历完成”标记；验收口径是 roadmap 固定关卡：Rule 原子性审核（已完成主体）→ 真实 QA 验收 → 逐 Feature review→published。
- Membership / Permission / Update 规则齐全且 published；Archive / Restore 规则齐全但整组 review；Creation 新旧混杂、治理资产大多未发布。
- 下一批扩库优先级候选：Join Request 生命周期、Permanent Delete、ABAC 调用路径核清、Creation 上限意图补齐。
