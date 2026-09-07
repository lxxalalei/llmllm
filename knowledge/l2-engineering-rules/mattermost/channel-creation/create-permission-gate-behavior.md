---
id: eng.mattermost.channel.creation.create_permission_gate.behavior
layer: L2
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.create_permission_gate.fact
behavior_rule_id: rule.mattermost.channel.creation.create_permission_gate
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- developer
- test
---

# 公开/私有频道创建由对应权限门禁

标准频道创建不是统一的“有登录态即可创建”。API 按公开/私有类型分别校验创建权限，并在进入 App 创建逻辑前拒绝缺少团队、显示名或使用错误创建入口的请求。
