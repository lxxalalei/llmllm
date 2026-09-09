---
id: eng.mattermost.channel.creation.team_channel_limit.fact
layer: L1
module: mattermost.channel
feature: channel_creation
status: published
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  commit: 86088592790eb63047bee73cd82390aae0c3e27b
  file: server/channels/app/channel.go
  symbol: CreateChannelWithUser
visible_roles: [developer, test]
---

# 团队频道创建受 MaxChannelsPerTeam 数量上限约束

`CreateChannelWithUser` 创建前先调用 `GetNumberOfChannelsOnTeam` 读取当前团队频道数；当 `count+1 > *Config().TeamSettings.MaxChannelsPerTeam` 时返回错误 `api.channel.create_channel.max_channel_limit.app_error`（HTTP 400），频道不落库。
