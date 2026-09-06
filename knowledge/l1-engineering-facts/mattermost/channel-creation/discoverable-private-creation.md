---
id: eng.mattermost.channel.creation.discoverable_private_creation.fact
layer: L1
module: mattermost.channel
feature: channel_creation
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: createChannel
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- developer
- test
---

# 可发现私有频道创建有额外门禁

创建 `Discoverable=true` 的频道时，DiscoverableChannels feature flag 必须开启，频道类型必须是 Private，并且请求者必须具有团队范围的 `manage_private_channel_discoverability` 权限；否则请求在创建前被拒绝。
