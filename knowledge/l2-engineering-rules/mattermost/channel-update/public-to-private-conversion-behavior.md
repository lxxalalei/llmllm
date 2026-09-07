---
id: eng.mattermost.channel.update.public_to_private_conversion.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.privacy_conversion.fact
behavior_rule_id: rule.mattermost.channel.update.public_to_private_conversion
tags: [mattermost, channel, channel_update]
visible_roles: [developer, test]
---

# 公开频道转私有使用专用转换权限

Open→Private 需要 `convert_public_channel_to_private`。Town Square 明确禁止转为 Private；类型更新后会写 privacy system post，如果该 post 失败则恢复转换前的频道类型和 discoverable 状态。
