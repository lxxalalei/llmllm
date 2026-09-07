---
id: eng.mattermost.channel.permission.base_scheme_invariant.behavior
layer: L2
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- eng.mattermost.channel.permission.base_scheme_invariant.fact
behavior_rule_id: rule.mattermost.channel.permission.base_scheme_invariant
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- developer
- test
---

# 常规角色更新必须保留成员基础 Scheme 身份

常规成员角色更新必须保证成员至少保留一种基础 scheme 身份。bulk import 的绕过是内部两阶段导入例外，不应被理解为普通角色管理也允许无基础角色成员。
