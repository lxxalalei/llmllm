---
id: eng.mattermost.channel.update.generic_update_guard_and_event.fact
layer: L1
module: mattermost.channel
feature: channel_update
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: updateChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: UpdateChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/guarded_hooks.go
  symbol: runGuardedChannelWillBeUpdated
tags:
- mattermost
- channel
- channel_update
visible_roles:
- developer
- test
---

# 通用更新禁止归档频道改类型，并经过插件 guard

`updateChannel` 在 API 层拒绝已归档频道和 payload 中的 Type 变化。App `UpdateChannel` 对频道更新运行 `ChannelWillBeUpdated`；guard claimant 不可通过 replacement 改变 Channel.Type，guard 不可用/RPC 失败时 fail-closed。更新成功后非 Space 频道发布 `channel_updated` WebSocket；Space 跳过该聊天侧广播。
