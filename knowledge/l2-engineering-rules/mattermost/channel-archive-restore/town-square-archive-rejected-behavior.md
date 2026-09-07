---
id: eng.mattermost.channel.archive_restore.town_square_archive_rejected.behavior
layer: L2
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.archive_permission_and_default.fact
behavior_rule_id: rule.mattermost.channel.archive_restore.town_square_archive_rejected
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [developer, test]
---

# Town Square 默认频道禁止归档

默认 `town-square` 在 App 层被硬性保护；该限制与请求者是否拥有公开频道删除权限是两件事。
