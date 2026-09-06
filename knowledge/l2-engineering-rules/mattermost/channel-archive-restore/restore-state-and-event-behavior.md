---
id: eng.mattermost.channel.archive_restore.restore_state_and_event.behavior
layer: L2
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.restore_state_and_event.fact
behavior_rule_id: rule.mattermost.channel.archive_restore.restore_state_and_event
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- developer
- test
---

# 恢复会清除归档状态并广播 channel_restored

恢复的核心状态变化是清除 DeleteAt，并刷新缓存和客户端状态。Space backing channel 只恢复底层状态，不发标准聊天频道的 restored 事件/system post。
