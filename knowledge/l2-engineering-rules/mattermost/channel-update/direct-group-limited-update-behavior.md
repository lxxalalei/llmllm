---
id: eng.mattermost.channel.update.direct_group_limited_update.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.property_permission_by_type.fact
behavior_rule_id: rule.mattermost.channel.update.direct_group_limited_update
tags: [mattermost, channel, channel_update]
visible_roles: [developer, test]
---

# Direct/Group 只允许成员执行有限字段更新

Direct/Group 没有普通频道的属性管理权限模型。只有频道成员可进入有限更新，而且 Name、DisplayName、Purpose 明确不可通过通用频道更新接口修改。
