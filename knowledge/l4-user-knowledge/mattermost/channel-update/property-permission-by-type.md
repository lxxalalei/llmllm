---
id: faq.mattermost.channel.update.property_permission_by_type
layer: L4
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- product.mattermost.channel.update.property_permission_by_type
behavior_rule_id: rule.mattermost.channel.update.property_permission_by_type
tags:
- mattermost
- channel
- channel_update
visible_roles:
- user
- product
- test
- developer
- admin
---

# 为什么我能修改频道头部信息，却不能给群聊改频道名称？

私聊/群聊和普通频道使用不同的更新规则。普通频道有专门的属性管理权限，而私聊/群聊只允许有限字段变化，不能通过通用频道接口改名称或用途。
