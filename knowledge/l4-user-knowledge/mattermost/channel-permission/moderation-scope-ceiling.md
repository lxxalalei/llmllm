---
id: faq.mattermost.channel.permission.moderation_scope_ceiling
layer: L4
module: mattermost.channel
feature: channel_permission
status: review
version: 1
derived_from:
- product.mattermost.channel.permission.moderation_scope_ceiling
behavior_rule_id: rule.mattermost.channel.permission.moderation_scope_ceiling
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- user
- product
- test
- developer
- admin
---

# 为什么某个频道权限开关不能被打开？

频道级权限不能突破上级角色的权限上限。如果团队/上级角色本身没有这项能力，频道不能单独把它授予成员或访客。
