---
id: product.mattermost.channel.update.property_permission_by_type
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.property_permission_by_type.behavior
behavior_rule_id: rule.mattermost.channel.update.property_permission_by_type
tags:
- mattermost
- channel
- channel_update
visible_roles:
- product
- test
- developer
- admin
---

# 频道属性修改权限随频道类型变化

修改公开频道和私有频道属性需要不同权限；私聊和群聊不支持像普通频道那样修改名称、显示名或用途。
