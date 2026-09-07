---
id: eng.mattermost.channel.membership.member_add_type_boundary.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_integrity_constraints.fact
behavior_rule_id: rule.mattermost.channel.membership.member_add_type_boundary
tags: [mattermost, channel, channel_membership]
visible_roles: [developer, test]
---

# 普通成员添加只接受 Open、Private 和 Space

`addUserToChannel` 的普通成员添加路径仅接受 Open、Private、Space；其他频道类型不会进入同一持久化流程。
