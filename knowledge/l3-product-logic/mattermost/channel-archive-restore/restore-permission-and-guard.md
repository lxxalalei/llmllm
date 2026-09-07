---
id: product.mattermost.channel.archive_restore.restore_permission_and_guard
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.restore_permission_and_guard.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.restore_permission_and_guard
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

# 恢复归档频道需要团队管理或系统频道管理权限

只有团队管理员或具有对应系统频道管理能力的用户才能恢复归档频道；未归档频道不能重复“恢复”。
