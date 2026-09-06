---
id: eng.mattermost.channel.permission.manage_member_roles.behavior
layer: L2
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- eng.mattermost.channel.permission.manage_member_roles.fact
behavior_rule_id: rule.mattermost.channel.permission.manage_member_roles
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- developer
- test
---

# 修改频道成员角色需要 manage_channel_roles

成员角色修改是频道级管理能力，普通成员不能仅凭自己属于频道就修改他人或自己的角色。REST 的显式门禁是 `manage_channel_roles`。
