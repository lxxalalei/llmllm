---
id: eng.mattermost.channel.update.unsupported_property_update_type.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: published
version: 1
derived_from:
- eng.mattermost.channel.update.property_permission_by_type.fact
behavior_rule_id: rule.mattermost.channel.update.unsupported_property_update_type
tags: [mattermost, channel, channel_update]
visible_roles: [developer, test]
---

# 未知频道类型拒绝通用属性更新

通用更新只为已定义的 Open、Private、Direct、Group 路径提供行为；其他未知类型直接拒绝，而不是退化到某个默认权限模型。
