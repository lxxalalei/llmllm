---
id: product.mattermost.channel.archive_restore.archive_permission_and_default
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.archive_permission_and_default.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.archive_permission_and_default
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- product
- test
- developer
- admin
---

# 归档频道按类型校验删除权限且保护默认频道

归档公开频道和私有频道需要各自的删除/归档权限；系统默认频道不能被归档。
