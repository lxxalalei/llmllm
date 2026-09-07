---
id: product.mattermost.channel.archive_restore.restore_state_and_event
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.restore_state_and_event.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.restore_state_and_event
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- product
- test
- developer
- admin
---

# 恢复会清除归档状态并广播 channel_restored

频道恢复后会重新变为活动频道并通知相关客户端；内部 Space backing channel 不走普通聊天频道的恢复提示流程。
