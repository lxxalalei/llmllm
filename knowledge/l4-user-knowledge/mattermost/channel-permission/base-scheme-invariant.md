---
id: faq.mattermost.channel.permission.base_scheme_invariant
layer: L4
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- product.mattermost.channel.permission.base_scheme_invariant
behavior_rule_id: rule.mattermost.channel.permission.base_scheme_invariant
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

# 为什么角色接口不允许把成员的基础角色全部去掉？

因为频道成员必须保留基础成员身份。普通角色修改不能让成员同时失去普通成员和访客这两类基础身份。
