---
id: product.mattermost.channel.permission.base_scheme_invariant
layer: L3
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- eng.mattermost.channel.permission.base_scheme_invariant.behavior
behavior_rule_id: rule.mattermost.channel.permission.base_scheme_invariant
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- product
- test
- developer
- admin
---

# 常规角色更新必须保留成员基础 Scheme 身份

正常修改频道成员角色时，系统不会允许把成员改成既不是普通成员也不是访客的无基础身份；批量导入有专用内部例外。
