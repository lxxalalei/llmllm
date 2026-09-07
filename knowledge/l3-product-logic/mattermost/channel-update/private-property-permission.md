---
id: product.mattermost.channel.update.private_property_permission
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.private_property_permission.behavior
behavior_rule_id: rule.mattermost.channel.update.private_property_permission
tags: [mattermost, channel, channel_update]
visible_roles: [product, test, developer, admin]
---

# 私有频道属性管理使用另一项独立权限

私有频道属性更新由 `manage_private_channel_properties` 控制，不能从公开频道属性权限推导。
