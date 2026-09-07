---
id: eng.mattermost.channel.permission.moderation_scope_ceiling.behavior
layer: L2
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- eng.mattermost.channel.permission.moderation_scope_ceiling.fact
behavior_rule_id: rule.mattermost.channel.permission.moderation_scope_ceiling
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- developer
- test
---

# 频道 moderation 不能授予高于上级角色的权限

频道级 moderation 是对上级权限的受限定制，不能越权创造上级角色没有的能力；当定制结果等同上级时，专用 scheme 会被消除以回到继承状态。
