---
id: eng.mattermost.channel.create.websocket_event
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

# 频道创建后发布 WebSocket 创建事件

`CreateChannelWithUser` 发布 `WebsocketEventChannelCreated`，事件中包含 `channel_id` 与 `team_id`，并以创建者 `userID` 作为事件目标用户。
