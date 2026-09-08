---
id: product.mattermost.channel.creation.standard_create_required_fields
layer: L3
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
- eng.mattermost.channel.creation.standard_create_required_fields.behavior
behavior_rule_id: rule.mattermost.channel.creation.standard_create_required_fields
tags: [mattermost, channel, channel_creation]
visible_roles: [product, test, developer, admin]
---

# 标准频道创建需要明确团队和频道名称

标准团队频道不是无归属对象：创建请求必须明确所属团队，并提供频道显示名称后才能继续创建。
