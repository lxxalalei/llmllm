---
id: product.mattermost.channel.archive_restore.open_archive_permission
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.open_archive_permission.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.open_archive_permission
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [product, test, developer, admin]
---

# 公开频道归档有自己的权限

归档公开频道需要 `delete_public_channel`；拥有其他频道管理能力不能替代这一权限。
