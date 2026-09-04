---
id: eng.mattermost.channel.create.join_message
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

# 创建频道后会发布创建者加入频道的系统消息

频道创建和默认分类处理完成后，`CreateChannelWithUser` 获取创建者用户并调用 `postJoinChannelMessage`。
