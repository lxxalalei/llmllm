---
id: eng.mattermost.channel.creation.create_private_permission.behavior
layer: L2
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
- eng.mattermost.channel.creation.create_permission_gate.fact
behavior_rule_id: rule.mattermost.channel.creation.create_private_permission
tags: [mattermost, channel, channel_creation]
visible_roles: [developer, test]
---

# 创建私有频道需要 create_private_channel

标准私有频道创建入口只在登录会话且请求者拥有团队范围的 `create_private_channel` 权限时通过私有频道权限门禁。
