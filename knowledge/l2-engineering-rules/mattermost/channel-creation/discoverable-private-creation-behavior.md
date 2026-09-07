---
id: eng.mattermost.channel.creation.discoverable_private_creation.behavior
layer: L2
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.discoverable_private_creation.fact
behavior_rule_id: rule.mattermost.channel.creation.discoverable_private_creation
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- developer
- test
---

# 可发现私有频道创建有额外门禁

可发现性不是普通频道字段的无条件写入。创建阶段同时受 feature flag、Private 类型和专用管理权限约束，且权限在频道尚未创建时按 Team scope 校验。
