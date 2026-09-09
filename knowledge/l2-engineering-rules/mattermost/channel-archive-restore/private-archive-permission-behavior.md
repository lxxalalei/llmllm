---
id: eng.mattermost.channel.archive_restore.private_archive_permission.behavior
layer: L2
module: mattermost.channel
feature: channel_archive_restore
status: published
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.archive_permission_and_default.fact
behavior_rule_id: rule.mattermost.channel.archive_restore.private_archive_permission
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [developer, test]
---

# 归档私有频道需要 delete_private_channel

标准 Private 频道归档请求需要 `delete_private_channel`，且目标必须仍处于未归档状态。
