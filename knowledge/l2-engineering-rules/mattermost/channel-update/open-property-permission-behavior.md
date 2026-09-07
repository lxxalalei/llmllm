---
id: eng.mattermost.channel.update.open_property_permission.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.property_permission_by_type.fact
behavior_rule_id: rule.mattermost.channel.update.open_property_permission
tags: [mattermost, channel, channel_update]
visible_roles: [developer, test]
---

# 公开频道属性更新需要 manage_public_channel_properties

Open 频道的通用属性更新由 `manage_public_channel_properties` 独立门禁控制。
