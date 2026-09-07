---
id: faq.mattermost.channel.membership.add_integrity_constraints
layer: L4
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- product.mattermost.channel.membership.add_integrity_constraints
behavior_rule_id: rule.mattermost.channel.membership.add_integrity_constraints
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

# 为什么管理员有权限加人，系统仍然提示这个用户不能加入？

“有加人权限”只说明你可以发起成员操作。目标用户还必须满足频道的成员条件，例如属于对应团队、满足群组限制等；这些条件不满足时仍会被拒绝。
