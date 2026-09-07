---
id: product.mattermost.channel.update.direct_group_limited_update
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.direct_group_limited_update.behavior
behavior_rule_id: rule.mattermost.channel.update.direct_group_limited_update
tags: [mattermost, channel, channel_update]
visible_roles: [product, test, developer, admin]
---

# 私聊和群聊不采用普通频道的属性管理方式

Direct/Group 只允许成员做有限更新，不能通过普通频道更新入口修改名称、显示名称或用途。
