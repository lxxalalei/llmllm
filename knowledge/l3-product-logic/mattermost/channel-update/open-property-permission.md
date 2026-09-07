---
id: product.mattermost.channel.update.open_property_permission
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.open_property_permission.behavior
behavior_rule_id: rule.mattermost.channel.update.open_property_permission
tags: [mattermost, channel, channel_update]
visible_roles: [product, test, developer, admin]
---

# 公开频道属性管理是一项独立权限

拥有频道访问权不等于可以修改公开频道属性；公开频道属性更新由 `manage_public_channel_properties` 控制。
