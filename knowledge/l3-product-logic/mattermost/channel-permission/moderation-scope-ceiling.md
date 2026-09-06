---
id: product.mattermost.channel.permission.moderation_scope_ceiling
layer: L3
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- eng.mattermost.channel.permission.moderation_scope_ceiling.behavior
behavior_rule_id: rule.mattermost.channel.permission.moderation_scope_ceiling
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- product
- test
- developer
- admin
---

# 频道 moderation 不能授予高于上级角色的权限

频道可以单独收紧或调整允许的权限，但不能给成员或访客增加其上级角色本来没有的权限。配置恢复成上级默认值后，频道会重新使用继承权限。
