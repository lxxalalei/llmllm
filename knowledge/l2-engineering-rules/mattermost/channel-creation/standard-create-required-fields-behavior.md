---
id: eng.mattermost.channel.creation.standard_create_required_fields.behavior
layer: L2
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
- eng.mattermost.channel.creation.create_permission_gate.fact
behavior_rule_id: rule.mattermost.channel.creation.standard_create_required_fields
tags: [mattermost, channel, channel_creation]
visible_roles: [developer, test]
---

# 普通频道创建必须提供 TeamId 和 DisplayName

普通 `/channels` 创建请求必须提供所属团队和频道显示名称；缺少这些必要字段时请求不会进入正常创建流程。
