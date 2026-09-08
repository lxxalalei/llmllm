# Legacy Creation 迁移审计 — 2026-09-08

目的：治理发布前，梳理 serve 面 legacy published（旧 channel.create 链）与 governed（review）资产的同一用户意图重叠，确定退役/保留。

## Serve 面 published（8 条，全为 legacy channel.create 命名空间）

| 资产 | 用户意图 | 治理同意图资产 | 处置建议 |
|---|---|---|---|
| faq.create.limit | 团队频道数量上限，不能继续创建 | 治理 creation 域**暂无独立上限意图 FAQ**（creator_membership FAQ 仅附属提及） | **保留 serve**；上限主题建议补为治理 creation 下一个 L4 意图 |
| faq.create.channel_limit_source | 上限由什么配置决定 | 同上 | **保留 serve** |
| faq.create.creator_auto_join | 创建后自动成为成员 | review: creation.creator_membership / creation_side_effects | 治理 creation 发布后退役 |
| faq.create.default_category | 新频道进默认分类 | review: creation_side_effects（同覆盖） | 治理 creation 发布后退役 |
| faq.create.join_message | 创建后的加入系统消息 | review: creation_side_effects（同覆盖） | 治理 creation 发布后退役 |
| faq.create.channel_types | 可创建类型（公开/私有；DM/GM/Board/Space 排除） | review: creation.create_permission_gate（部分） | 治理 creation 发布后退役 |
| faq.create.channel_belongs_to_team | 频道必须归属团队 | review: creation 原子规则（team 归属语义） | 治理 creation 发布后退役 |
| product.create.team_channel（L3） | 创建团队频道产品逻辑（user 不可见） | review: creation L3 ×9 | 治理 creation 发布后退役 |

## 结论
- 无治理冲突可直接保留：2 条上限 FAQ（上限主题在治理侧缺失，建议补意图）。
- 6 条与治理同意图重叠：在 creation Feature 通过 QA 并发布时随发布退役（进入 deprecated 或删除，走发布流程钩子，不整批手改）。
- membership / permission / update / archive_restore 域旧链无 published 重叠，可独立逐 Feature 发布（无旧资产退役负担）。

## 待产品决策
1. “频道数量上限”是否补为治理 creation 的新 L4 意图（推荐：是，作为下一批 Knowledge 优先级）；
2. legacy 6 条重叠项退役方式：随治理发布置 deprecated（可追溯）还是直接删除。
