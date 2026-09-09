---
id: product.mattermost.channel.archive_restore.standard_archive_type_boundary
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: published
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.standard_archive_type_boundary.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.standard_archive_type_boundary
tags: [mattermost, channel, channel_archive_restore]
visible_roles: [product, test, developer, admin]
---

# 标准频道归档入口只覆盖公开/私有频道

普通频道归档 API 的权限模型只面向 Open/Private；其他频道类型不能默认沿用这套标准入口规则。
