---
id: product.mattermost.channel.archive_restore.private_archive_permission
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.private_archive_permission.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.private_archive_permission
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [product, test, developer, admin]
---

# 私有频道归档使用另一项权限

归档私有频道需要 `delete_private_channel`，与公开频道归档权限独立。
