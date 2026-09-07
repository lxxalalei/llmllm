---
id: eng.mattermost.channel.creation.standard_create_type_boundary.behavior
layer: L2
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.create_permission_gate.fact
behavior_rule_id: rule.mattermost.channel.creation.standard_create_type_boundary
tags: [mattermost, channel, channel_creation]
visible_roles: [developer, test]
---

# 普通频道创建入口拒绝非标准团队频道类型

Direct、Group、Board 和 Space 不通过普通团队频道创建入口建立；这些类型必须走各自专用流程。
