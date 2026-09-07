---
id: faq.mattermost.channel.archive_restore.restore_state_and_event
layer: L4
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- product.mattermost.channel.archive_restore.restore_state_and_event
behavior_rule_id: rule.mattermost.channel.archive_restore.restore_state_and_event
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

# 恢复频道后，客户端为什么会自动重新出现频道？

恢复会清除频道的归档状态并发送频道恢复事件，客户端收到后会刷新频道状态。
