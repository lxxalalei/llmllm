---
id: eng.mattermost.channel.archive_restore.already_archived_rejected.behavior
layer: L2
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.archive_permission_and_default.fact
behavior_rule_id: rule.mattermost.channel.archive_restore.already_archived_rejected
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [developer, test]
---

# 已归档频道不能重复归档

App `DeleteChannel` 在目标已经存在归档时间时直接拒绝，不会重复写归档状态。
