---
id: product.mattermost.channel.creation.creation_side_effects
layer: L3
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.creation_side_effects.behavior
behavior_rule_id: rule.mattermost.channel.creation.creation_side_effects
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- product
- test
- developer
- admin
---

# 标准频道创建会触发聊天侧生命周期副作用

标准频道创建成功后，不只是新增一条频道记录：创建者的侧边栏分类、频道内加入提示以及客户端新频道状态都会同步更新，并触发频道创建生命周期扩展。
