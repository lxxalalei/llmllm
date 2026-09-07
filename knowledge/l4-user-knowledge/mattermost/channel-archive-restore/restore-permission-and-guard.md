---
id: faq.mattermost.channel.archive_restore.restore_permission_and_guard
layer: L4
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- product.mattermost.channel.archive_restore.restore_permission_and_guard
behavior_rule_id: rule.mattermost.channel.archive_restore.restore_permission_and_guard
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- user
- product
- test
- developer
- admin
---

# 谁可以恢复已经归档的频道？

通常需要团队管理权限；具备相应系统频道管理能力的管理员也可以执行恢复。频道必须当前处于已归档状态。
