---
id: eng.mattermost.channel.create.team_limit
layer: L1
module: mattermost.channel
feature: channel_creation
status: draft
version: 1
sources:
  - repo: mattermost/mattermost
    ref: master
    commit: 43b2ae87e06b06abe01f9382ec26899c54c31728
    file: server/channels/app/channel.go
    symbol: CreateChannelWithUser
visible_roles: [developer, test]
---

# 团队频道数量受 MaxChannelsPerTeam 限制

创建前会读取当前团队频道数；若新增一个频道后超过 `TeamSettings.MaxChannelsPerTeam`，创建被拒绝。
