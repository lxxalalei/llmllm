---
id: eng.mattermost.channel.update.discoverability_patch_gate.fact
layer: L1
module: mattermost.channel
feature: channel_update
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: patchChannel
tags:
- mattermost
- channel
- channel_update
visible_roles:
- developer
- test
---

# 私有频道可发现性修改受类型、共享状态和权限限制

`patchChannel` 在修改 Discoverable 时要求 DiscoverableChannels 功能可用；目标必须是 Private，Shared channel 不允许该修改，并要求频道范围 `manage_private_channel_discoverability` 权限。创建阶段同一能力使用 team-scope 权限，因为当时尚无 channel-scope grant。
