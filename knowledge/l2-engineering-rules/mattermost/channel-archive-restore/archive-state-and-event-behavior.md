---
id: eng.mattermost.channel.archive_restore.archive_state_and_event.behavior
layer: L2
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.archive_state_and_event.fact
behavior_rule_id: rule.mattermost.channel.archive_restore.archive_state_and_event
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- developer
- test
---

# 归档写入 DeleteAt 并广播频道删除事件

归档是软删除状态变化，并带有可拒绝的插件前置 hook 和客户端事件。公开频道与非公开频道的 WebSocket 广播范围不同；Space 不走标准聊天生命周期。
