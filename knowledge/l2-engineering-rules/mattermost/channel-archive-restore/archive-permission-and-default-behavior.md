---
id: eng.mattermost.channel.archive_restore.archive_permission_and_default.behavior
layer: L2
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.archive_permission_and_default.fact
behavior_rule_id: rule.mattermost.channel.archive_restore.archive_permission_and_default
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- developer
- test
---

# 归档频道按类型校验删除权限且保护默认频道

频道归档权限按公开/私有类型区分，并存在不可归档的默认频道保护。已经归档的频道不能重复归档。
