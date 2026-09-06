---
id: product.mattermost.channel.membership.add_permission_split
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_permission_split.behavior
behavior_rule_id: rule.mattermost.channel.membership.add_permission_split
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- product
- test
- developer
- admin
---

# 加入自己与添加他人使用不同权限

在公开频道中，用户自己加入和把别人加入频道是两种不同权限。私有频道则要求私有频道成员管理权限，普通频道成员接口也不能用于私聊或群聊。
