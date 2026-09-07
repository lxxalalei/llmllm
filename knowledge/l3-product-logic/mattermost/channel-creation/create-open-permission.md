---
id: product.mattermost.channel.creation.create_open_permission
layer: L3
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.create_open_permission.behavior
behavior_rule_id: rule.mattermost.channel.creation.create_open_permission
tags: [mattermost, channel, channel_creation]
visible_roles: [product, test, developer, admin]
---

# 创建公开频道使用独立权限

用户能否创建公开频道由 `create_public_channel` 权限单独决定，不应从私有频道创建权限推导。
