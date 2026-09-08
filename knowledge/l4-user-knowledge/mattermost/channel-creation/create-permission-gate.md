---
id: faq.mattermost.channel.creation.create_permission_gate
layer: L4
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
- product.mattermost.channel.creation.create_open_permission
- product.mattermost.channel.creation.create_private_permission
- product.mattermost.channel.creation.standard_create_type_boundary
behavior_rule_ids:
- rule.mattermost.channel.creation.create_open_permission
- rule.mattermost.channel.creation.create_private_permission
- rule.mattermost.channel.creation.standard_create_type_boundary
tags: [mattermost, channel, channel_creation]
visible_roles: [user, product, test, developer, admin]
---

# 为什么有的人能创建公开频道却不能创建私有频道？

公开频道和私有频道使用不同的创建权限。即使你能创建一种频道，也不代表自动拥有另一种频道的创建权限；另外，私聊、群聊、Board、Space 也不是通过普通频道创建入口建立的。
