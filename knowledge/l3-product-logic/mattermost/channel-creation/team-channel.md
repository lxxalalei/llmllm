---
id: product.mattermost.channel.create.team_channel
layer: L3
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
  - eng.mattermost.channel.create.standard_flow
  - eng.mattermost.channel.create.creator_membership_rule
visible_roles: [product, test, developer]
---

# 创建团队频道

## 当前从实现抽象出的产品逻辑

- 用户创建的是某个团队下的公开或私有频道。
- 团队达到频道数量上限后不能继续创建。
- 创建成功后，创建者会自动成为频道成员，并具备频道管理员标记。
- 新频道会加入创建者的默认频道分类。
- 创建成功会产生加入频道的系统消息，并触发客户端可接收的频道创建事件。

> 已发布（2026-09-05）：经产品审核批准，以上逻辑作为频道创建的产品行为进入普通用户知识层。
