---
id: product.mattermost.channel.membership.private_add_permission
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.private_add_permission.behavior
behavior_rule_id: rule.mattermost.channel.membership.private_add_permission
tags: [mattermost, channel, channel_membership]
visible_roles: [product, test, developer, admin]
---

# 私有频道加人使用私有成员管理权限

通过普通成员添加入口向私有频道添加成员时，需要私有频道成员管理权限；公开频道的加入权限不能替代它。
