---
id: product.mattermost.channel.update.space_privacy_conversion_rejected
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.space_privacy_conversion_rejected.behavior
behavior_rule_id: rule.mattermost.channel.update.space_privacy_conversion_rejected
tags: [mattermost, channel, channel_update]
visible_roles: [product, test, developer, admin]
---

# Space 不支持普通频道的公开/私有转换

Space 有独立对象语义，不参与 Open/Private 频道隐私转换流程。
