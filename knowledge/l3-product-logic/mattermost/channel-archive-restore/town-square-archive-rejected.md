---
id: product.mattermost.channel.archive_restore.town_square_archive_rejected
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.town_square_archive_rejected.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.town_square_archive_rejected
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [product, test, developer, admin]
---

# Town Square 是不可归档的默认频道

Town Square 的保护是独立产品规则，即使操作者具备普通公开频道的归档权限，也不能归档该默认频道。
