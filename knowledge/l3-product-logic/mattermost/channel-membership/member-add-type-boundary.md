---
id: product.mattermost.channel.membership.member_add_type_boundary
layer: L3
module: mattermost.channel
feature: channel_membership
status: published
version: 1
derived_from:
- eng.mattermost.channel.membership.member_add_type_boundary.behavior
behavior_rule_id: rule.mattermost.channel.membership.member_add_type_boundary
tags: [mattermost, channel, channel_membership]
visible_roles: [product, test, developer, admin]
---

# 普通频道成员添加不覆盖所有会话类型

标准成员添加流程只面向 Open、Private、Space；其他会话或频道类型有自己的成员关系模型，不能套用同一入口。
