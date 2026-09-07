---
id: faq.mattermost.channel.membership.discoverable_self_add
layer: L4
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- product.mattermost.channel.membership.discoverable_self_add
behavior_rule_id: rule.mattermost.channel.membership.discoverable_self_add
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- user
- product
- test
- developer
- admin
---

# 为什么我能看到一个私有频道，却不能直接加入？

因为“可发现”只表示你可以发现这个私有频道，不等于可以直接成为成员。当前配置下，自助加入需要通过加入申请流程。
