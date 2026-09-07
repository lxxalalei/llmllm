---
id: product.mattermost.channel.update.unsupported_property_update_type
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.unsupported_property_update_type.behavior
behavior_rule_id: rule.mattermost.channel.update.unsupported_property_update_type
tags: [mattermost, channel, channel_update]
visible_roles: [product, test, developer, admin]
---

# 未定义频道类型不会套用默认属性更新规则

系统只对明确支持的频道类型应用对应更新策略，未知类型直接拒绝，避免误用普通频道或会话的权限模型。
