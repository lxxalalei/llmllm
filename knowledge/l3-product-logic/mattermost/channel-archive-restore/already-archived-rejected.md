---
id: product.mattermost.channel.archive_restore.already_archived_rejected
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.already_archived_rejected.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.already_archived_rejected
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [product, test, developer, admin]
---

# 已归档频道不能再次执行归档

归档是一项状态转换，只对当前未归档频道成立；已经归档的频道不会再次进入归档流程。
