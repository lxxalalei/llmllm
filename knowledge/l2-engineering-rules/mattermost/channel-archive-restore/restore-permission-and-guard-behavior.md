---
id: eng.mattermost.channel.archive_restore.restore_permission_and_guard.behavior
layer: L2
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.restore_permission_and_guard.fact
behavior_rule_id: rule.mattermost.channel.archive_restore.restore_permission_and_guard
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- developer
- test
---

# 恢复归档频道需要团队管理或系统频道管理权限

恢复不是普通成员操作：API 使用团队管理/系统频道管理权限，并且只允许恢复当前确实处于归档状态的频道。受 guard 保护的频道还必须通过恢复前置规则。
