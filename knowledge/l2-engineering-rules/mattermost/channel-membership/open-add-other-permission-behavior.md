---
id: eng.mattermost.channel.membership.open_add_other_permission.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_permission_split.fact
behavior_rule_id: rule.mattermost.channel.membership.open_add_other_permission
tags: [mattermost, channel, channel_membership]
visible_roles: [developer, test]
---

# 公开频道添加他人要求 manage_public_channel_members

当请求者与目标用户不同且频道类型为 Open 时，成员添加入口要求 `manage_public_channel_members`。拥有 `join_public_channels` 不足以替别人加人。
