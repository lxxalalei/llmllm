---
id: product.mattermost.channel.creation.standard_create_type_boundary
layer: L3
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.standard_create_type_boundary.behavior
behavior_rule_id: rule.mattermost.channel.creation.standard_create_type_boundary
tags: [mattermost, channel, channel_creation]
visible_roles: [product, test, developer, admin]
---

# 普通频道创建入口只负责标准团队频道

私聊、群聊、Board 和 Space 不属于普通团队频道创建流程，不能把这些对象的创建规则与公开/私有频道创建规则混在一起。
