---
id: faq.mattermost.channel.archive_restore.archive_state_and_event
layer: L4
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- product.mattermost.channel.archive_restore.archive_state_and_event
behavior_rule_id: rule.mattermost.channel.archive_restore.archive_state_and_event
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

# 频道归档后为什么会从客户端列表里消失，但不是永久删除？

普通归档会把频道标记为已删除/归档状态并通知客户端更新，而不是直接永久清除所有数据。
