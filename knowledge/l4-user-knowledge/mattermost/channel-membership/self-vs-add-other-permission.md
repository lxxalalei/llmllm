---
id: faq.mattermost.channel.membership.self_vs_add_other_permission
layer: L4
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- product.mattermost.channel.membership.open_self_add_permission
- product.mattermost.channel.membership.open_add_other_permission
behavior_rule_ids:
- rule.mattermost.channel.membership.open_self_add_permission
- rule.mattermost.channel.membership.open_add_other_permission
tags: [mattermost, channel, channel_membership]
visible_roles: [user, product, test, developer, admin]
---

# 为什么我能自己加入公开频道，却不能把别人加入？

因为这是两种不同权限。自己加入公开频道要求“加入公开频道”权限；替其他用户加入则要求“管理公开频道成员”权限。拥有前者不代表拥有后者。
