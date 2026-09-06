---
id: eng.mattermost.channel.creation.creation_side_effects.behavior
layer: L2
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.creation_side_effects.fact
behavior_rule_id: rule.mattermost.channel.creation.creation_side_effects
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- developer
- test
---

# 标准频道创建会触发聊天侧生命周期副作用

标准频道创建完成后还会同步用户侧分类、system post、WebSocket 和 plugin lifecycle；Space backing channel 明确不走标准聊天插件生命周期。
