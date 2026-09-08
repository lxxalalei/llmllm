---
id: product.mattermost.channel.creation.create_private_permission
layer: L3
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
- eng.mattermost.channel.creation.create_private_permission.behavior
behavior_rule_id: rule.mattermost.channel.creation.create_private_permission
tags: [mattermost, channel, channel_creation]
visible_roles: [product, test, developer, admin]
---

# 创建私有频道使用独立权限

用户能否创建私有频道由 `create_private_channel` 权限单独决定，不应从公开频道创建权限推导。
