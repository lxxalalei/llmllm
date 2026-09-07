---
id: eng.mattermost.channel.membership.group_constrained_membership.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_integrity_constraints.fact
behavior_rule_id: rule.mattermost.channel.membership.group_constrained_membership
tags: [mattermost, channel, channel_membership]
visible_roles: [developer, test]
---

# GroupConstrained 频道独立校验群组成员资格

当频道受群组约束时，目标用户还必须通过 `FilterNonGroupChannelMembers` 的群组条件；权限检查通过并不能绕过这一约束。
