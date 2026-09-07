---
id: eng.mattermost.channel.membership.open_self_add_permission.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_permission_split.fact
behavior_rule_id: rule.mattermost.channel.membership.open_self_add_permission
tags: [mattermost, channel, channel_membership]
visible_roles: [developer, test]
---

# 公开频道自助加入要求 join_public_channels

当请求者与目标用户相同且频道类型为 Open 时，成员添加入口按自助加入处理，要求 `join_public_channels`，而不是公开频道成员管理权限。
