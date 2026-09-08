---
id: eng.mattermost.channel.update.space_privacy_conversion_rejected.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: published
version: 1
derived_from:
- eng.mattermost.channel.update.privacy_conversion.fact
behavior_rule_id: rule.mattermost.channel.update.space_privacy_conversion_rejected
tags: [mattermost, channel, channel_update]
visible_roles: [developer, test]
---

# Space 不进入普通频道隐私转换流程

App 层明确拒绝对 Space 执行 Open/Private privacy conversion，不能把 Space 当成普通团队频道转换。
