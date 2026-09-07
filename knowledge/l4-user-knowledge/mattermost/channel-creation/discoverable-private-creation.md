---
id: faq.mattermost.channel.creation.discoverable_private_creation
layer: L4
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- product.mattermost.channel.creation.discoverable_private_creation
behavior_rule_id: rule.mattermost.channel.creation.discoverable_private_creation
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- user
- product
- test
- developer
- admin
---

# 为什么创建频道时不能开启“可发现”？

“可发现”只适用于私有频道，并且系统需要启用这一功能；创建者还必须具备管理私有频道可发现性的权限。
