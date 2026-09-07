---
id: eng.mattermost.channel.membership.private_add_permission.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_permission_split.fact
behavior_rule_id: rule.mattermost.channel.membership.private_add_permission
tags: [mattermost, channel, channel_membership]
visible_roles: [developer, test]
---

# 私有频道添加成员要求 manage_private_channel_members

Private 频道的普通成员添加入口要求 `manage_private_channel_members`。它不复用公开频道的自助加入或公开成员管理权限。
