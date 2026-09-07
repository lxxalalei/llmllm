---
id: product.mattermost.channel.membership.member_add_guarded_hook
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.member_add_guarded_hook.behavior
behavior_rule_id: rule.mattermost.channel.membership.member_add_guarded_hook
tags: [mattermost, channel, channel_membership]
visible_roles: [product, test, developer, admin]
---

# 非 Space 频道成员写入还受成员加入 guard 约束

通过前置权限和成员资格检查后，非 Space 频道在真正保存成员关系前还会经过 `ChannelMemberWillBeAdded` 规则；Space 不走这条标准聊天侧 guard。
