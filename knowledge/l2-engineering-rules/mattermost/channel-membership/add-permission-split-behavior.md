---
id: eng.mattermost.channel.membership.add_permission_split.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_permission_split.fact
behavior_rule_id: rule.mattermost.channel.membership.add_permission_split
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 加入自己与添加他人使用不同权限

频道成员添加权限与 actor/target 关系绑定。公开频道的自助加入和管理员加人不是同一权限；私有频道成员管理使用私有频道成员管理权限；Direct/Group 不走该接口。
