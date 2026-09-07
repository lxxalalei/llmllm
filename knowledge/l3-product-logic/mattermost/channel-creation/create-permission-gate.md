---
id: product.mattermost.channel.creation.create_permission_gate
layer: L3
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.create_permission_gate.behavior
behavior_rule_id: rule.mattermost.channel.creation.create_permission_gate
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

# 公开/私有频道创建由对应权限门禁

创建公开频道和私有频道需要不同的创建权限；普通频道接口只处理标准团队频道，不负责私聊、群聊、Board 或 Space 的专用创建流程。
