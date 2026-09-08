---
id: product.mattermost.channel.membership.open_self_add_permission
layer: L3
module: mattermost.channel
feature: channel_membership
status: published
version: 1
derived_from:
- eng.mattermost.channel.membership.open_self_add_permission.behavior
behavior_rule_id: rule.mattermost.channel.membership.open_self_add_permission
tags: [mattermost, channel, channel_membership]
visible_roles: [product, test, developer, admin]
---

# 公开频道自助加入要求加入公开频道权限

用户把自己加入公开频道时，系统检查的是“加入公开频道”权限。这与替其他用户管理频道成员是不同能力。
