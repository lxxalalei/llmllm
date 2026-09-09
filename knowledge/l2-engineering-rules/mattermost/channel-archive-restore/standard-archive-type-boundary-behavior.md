---
id: eng.mattermost.channel.archive_restore.standard_archive_type_boundary.behavior
layer: L2
module: mattermost.channel
feature: channel_archive_restore
status: published
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.archive_permission_and_default.fact
behavior_rule_id: rule.mattermost.channel.archive_restore.standard_archive_type_boundary
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [developer, test]
---

# 标准归档 API 只处理公开/私有频道

普通 `deleteChannel` API 的频道归档路径只接受标准 Open/Private 频道；其他类型不应被套用到该接口的权限分支。
