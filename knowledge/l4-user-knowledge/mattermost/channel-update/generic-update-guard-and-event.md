---
id: faq.mattermost.channel.update.generic_update_guard_and_event
layer: L4
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- product.mattermost.channel.update.generic_update_guard_and_event
behavior_rule_id: rule.mattermost.channel.update.generic_update_guard_and_event
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

# 为什么普通“编辑频道”不能顺便把公开频道改成私有频道？

频道类型转换是独立操作，不能混在普通属性更新里。这样类型转换使用自己的权限和后续处理流程。
