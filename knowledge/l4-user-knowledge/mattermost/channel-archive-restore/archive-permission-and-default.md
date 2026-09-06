---
id: faq.mattermost.channel.archive_restore.archive_permission_and_default
layer: L4
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- product.mattermost.channel.archive_restore.archive_permission_and_default
behavior_rule_id: rule.mattermost.channel.archive_restore.archive_permission_and_default
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- user
- product
- test
- developer
- admin
---

# 为什么我有频道管理权限，还是不能归档 Town Square？

Town Square 是系统默认频道，代码层明确禁止归档。其他频道是否能归档还取决于公开/私有频道对应的删除权限。
