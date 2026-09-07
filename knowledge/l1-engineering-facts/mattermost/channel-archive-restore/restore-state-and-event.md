---
id: eng.mattermost.channel.archive_restore.restore_state_and_event.fact
layer: L1
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: RestoreChannel
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- developer
- test
---

# 恢复会清除归档状态并广播 channel_restored

`RestoreChannel` 调用 Store `Channel().Restore` 后把 `channel.DeleteAt` 置 0 并失效频道缓存。Space 此时直接返回；非 Space 根据公开/非公开范围发送 `channel_restored` WebSocket，并继续执行聊天侧恢复处理。
