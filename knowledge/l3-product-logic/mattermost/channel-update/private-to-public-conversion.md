---
id: product.mattermost.channel.update.private_to_public_conversion
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.private_to_public_conversion.behavior
behavior_rule_id: rule.mattermost.channel.update.private_to_public_conversion
tags: [mattermost, channel, channel_update]
visible_roles: [product, test, developer, admin]
---

# 私有转公开会结束私有频道的申请语义

私有频道转公开需要独立权限；转换后频道不再保留私有可发现状态，原有待审批加入申请也会被撤回。转换记录失败时会回滚到之前状态。
