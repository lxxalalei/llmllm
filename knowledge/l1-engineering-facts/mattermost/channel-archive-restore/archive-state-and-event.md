---
id: eng.mattermost.channel.archive_restore.archive_state_and_event.fact
layer: L1
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: DeleteChannel
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- developer
- test
---

# 归档写入 DeleteAt 并广播频道删除事件

`DeleteChannel` 在非 Space 频道先运行 `ChannelWillBeArchived`，插件可返回 reason 阻止归档。通过后 Store `Channel().Delete(channel.Id, deleteAt)` 写入归档时间。非 Space 会写归档 system post；随后按 Open/Private 广播范围发送 `channel_deleted` WebSocket。Space backing channel 跳过标准聊天 hook/system post。
