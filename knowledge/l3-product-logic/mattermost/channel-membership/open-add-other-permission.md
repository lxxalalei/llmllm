---
id: product.mattermost.channel.membership.open_add_other_permission
layer: L3
module: mattermost.channel
feature: channel_membership
status: published
version: 1
derived_from:
- eng.mattermost.channel.membership.open_add_other_permission.behavior
behavior_rule_id: rule.mattermost.channel.membership.open_add_other_permission
tags: [mattermost, channel, channel_membership]
visible_roles: [product, test, developer, admin]
---

# 公开频道替别人加人要求成员管理权限

把其他用户加入公开频道属于成员管理操作，需要公开频道成员管理权限；能自己加入公开频道并不代表能替别人加人。
