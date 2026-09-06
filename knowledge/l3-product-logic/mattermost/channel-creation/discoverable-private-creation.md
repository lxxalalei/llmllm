---
id: product.mattermost.channel.creation.discoverable_private_creation
layer: L3
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.discoverable_private_creation.behavior
behavior_rule_id: rule.mattermost.channel.creation.discoverable_private_creation
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- product
- test
- developer
- admin
---

# 可发现私有频道创建有额外门禁

“可发现”只适用于私有频道，而且需要系统启用该能力并由拥有可发现性管理权限的人创建。
