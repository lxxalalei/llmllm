---
id: eng.mattermost.channel.update.property_permission_by_type.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.property_permission_by_type.fact
behavior_rule_id: rule.mattermost.channel.update.property_permission_by_type
tags:
- mattermost
- channel
- channel_update
visible_roles:
- developer
- test
---

# 频道属性修改权限随频道类型变化

标准公开/私有频道使用各自的属性管理权限。Direct/Group 不是普通频道属性管理模型，只允许成员进行有限字段更新，不能借通用更新接口重命名或修改 Purpose。
