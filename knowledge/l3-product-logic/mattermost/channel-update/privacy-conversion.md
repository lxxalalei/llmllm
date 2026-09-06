---
id: product.mattermost.channel.update.privacy_conversion
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.privacy_conversion.behavior
behavior_rule_id: rule.mattermost.channel.update.privacy_conversion
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

# 公开/私有转换使用专用权限并维护可发现申请状态

公开与私有频道互转需要专门权限。默认频道不能转成私有频道；私有可发现频道转公开后，不再保留“可发现私有频道”的申请状态，已有待审批加入请求会被撤回。
