---
id: product.mattermost.channel.update.generic_update_guard_and_event
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.generic_update_guard_and_event.behavior
behavior_rule_id: rule.mattermost.channel.update.generic_update_guard_and_event
tags:
- mattermost
- channel
- channel_update
visible_roles:
- product
- test
- developer
- admin
---

# 通用更新禁止归档频道改类型，并经过插件 guard

普通频道属性修改不能顺便改变频道类型，类型转换必须走专用流程。某些受插件保护的频道还会在保存前经过规则检查。
