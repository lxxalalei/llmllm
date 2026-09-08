---
id: eng.mattermost.channel.membership.member_add_guarded_hook.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: published
version: 1
derived_from:
- eng.mattermost.channel.membership.add_integrity_constraints.fact
behavior_rule_id: rule.mattermost.channel.membership.member_add_guarded_hook
tags: [mattermost, channel, channel_membership]
visible_roles: [developer, test]
---

# 非 Space 成员保存前运行 ChannelMemberWillBeAdded guard

普通频道成员关系在持久化前经过 `ChannelMemberWillBeAdded` guarded hook；Space 跳过这条标准聊天侧 hook。
