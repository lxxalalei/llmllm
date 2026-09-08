---
id: eng.mattermost.channel.membership.team_member_integrity.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: published
version: 1
derived_from:
- eng.mattermost.channel.membership.add_integrity_constraints.fact
behavior_rule_id: rule.mattermost.channel.membership.team_member_integrity
tags: [mattermost, channel, channel_membership]
visible_roles: [developer, test]
---

# 成员加入默认要求有效 TeamMember

`AddUserToChannel` 默认校验目标用户的团队成员关系；只有显式设置内部 skip 选项的路径才跳过这一项检查，不能把 skip 当成普通成员添加行为。
