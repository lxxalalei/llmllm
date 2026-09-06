---
id: eng.mattermost.channel.creation.creation_side_effects.fact
layer: L1
module: mattermost.channel
feature: channel_creation
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: CreateChannelWithUser
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: CreateChannel
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- developer
- test
---

# 标准频道创建会触发聊天侧生命周期副作用

`CreateChannelWithUser` 会把新频道加入创建者默认分类、发布加入频道 system post，并向创建者发送 `channel_created` WebSocket。非 Space 的 `CreateChannel` 还会异步触发 `ChannelHasBeenCreated` plugin hook；Space backing channel 跳过标准聊天 hook。
