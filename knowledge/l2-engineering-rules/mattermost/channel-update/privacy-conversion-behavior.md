---
id: eng.mattermost.channel.update.privacy_conversion.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.privacy_conversion.fact
behavior_rule_id: rule.mattermost.channel.update.privacy_conversion
tags:
- mattermost
- channel
- channel_update
visible_roles:
- developer
- test
---

# 公开/私有转换使用专用权限并维护可发现申请状态

频道公开/私有转换是独立事务语义：单独权限、默认频道保护、Space 排除、隐私变更提示和失败回滚。转为公开后，可发现申请队列失去意义，因此 pending 请求会被撤回。
