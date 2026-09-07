---
id: product.mattermost.channel.permission.manage_member_roles
layer: L3
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- eng.mattermost.channel.permission.manage_member_roles.behavior
behavior_rule_id: rule.mattermost.channel.permission.manage_member_roles
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- product
- test
- developer
- admin
---

# 修改频道成员角色需要 manage_channel_roles

修改频道成员角色需要频道角色管理权限，而不是普通频道成员身份。
