---
id: faq.mattermost.channel.permission.manage_member_roles
layer: L4
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- product.mattermost.channel.permission.manage_member_roles
behavior_rule_id: rule.mattermost.channel.permission.manage_member_roles
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- user
- product
- test
- developer
- admin
---

# 为什么我能管理频道内容，却不能把某个成员设为频道管理员？

成员角色属于单独的频道角色管理能力。能使用或管理频道内容，不代表你拥有修改成员角色的权限。
