---
id: faq.mattermost.channel.membership.add_permission_split
layer: L4
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- product.mattermost.channel.membership.add_permission_split
behavior_rule_id: rule.mattermost.channel.membership.add_permission_split
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

# 为什么我自己能加入公开频道，却不能把别人拉进来？

因为“加入公开频道”和“管理公开频道成员”是两项不同权限。你可以拥有自助加入权限，但没有替别人添加成员的权限。
