---
id: eng.mattermost.channel.create.team_required
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

# 创建团队频道必须提供 TeamId

`CreateChannelWithUser` 在 `channel.TeamId` 为空时直接返回 Bad Request，不继续创建。
