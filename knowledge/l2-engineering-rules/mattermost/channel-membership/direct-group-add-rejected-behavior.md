---
id: eng.mattermost.channel.membership.direct_group_add_rejected.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_permission_split.fact
behavior_rule_id: rule.mattermost.channel.membership.direct_group_add_rejected
tags: [mattermost, channel, channel_membership]
visible_roles: [developer, test]
---

# 普通成员添加接口拒绝 Direct 和 Group

普通频道成员添加 API 不承担 Direct/Group 会话成员创建；目标频道类型为 Direct 或 Group 时，该入口直接拒绝。
