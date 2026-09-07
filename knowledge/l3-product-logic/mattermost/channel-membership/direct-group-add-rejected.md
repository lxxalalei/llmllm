---
id: product.mattermost.channel.membership.direct_group_add_rejected
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.direct_group_add_rejected.behavior
behavior_rule_id: rule.mattermost.channel.membership.direct_group_add_rejected
tags: [mattermost, channel, channel_membership]
visible_roles: [product, test, developer, admin]
---

# 私聊和群聊不走普通频道加人入口

Direct 和 Group 会话不是通过普通频道成员添加入口扩充成员；使用该入口操作这两类会话会被拒绝。
