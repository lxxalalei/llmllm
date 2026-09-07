---
id: product.mattermost.channel.create.space_availability
layer: L3
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
  - eng.mattermost.channel.create.feature_gates
  - eng.mattermost.channel.create.standard_flow
visible_roles: [product, test, developer]
---

# Space 创建可用性

Space 不走普通团队频道的用户创建入口，并且底层创建要求 Docs 功能开关开启。未开启时创建会被拒绝。

> 已发布（2026-09-07）：经产品审核批准；如需产品口径差异说明，请另建资产更新。Space 的用户入口名称和对外产品文案需要产品审核确认。
