---
id: product.mattermost.channel.update.public_to_private_conversion
layer: L3
module: mattermost.channel
feature: channel_update
status: published
version: 1
derived_from:
- eng.mattermost.channel.update.public_to_private_conversion.behavior
behavior_rule_id: rule.mattermost.channel.update.public_to_private_conversion
tags: [mattermost, channel, channel_update]
visible_roles: [product, test, developer, admin]
---

# 公开转私有是独立受控操作

公开频道转私有需要专用转换权限，并且 Town Square 不能转为私有。系统消息写入也属于转换完整性的一部分，失败时转换会回滚。
