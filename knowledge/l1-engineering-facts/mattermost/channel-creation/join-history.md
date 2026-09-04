---
id: eng.mattermost.channel.create.join_history
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
    symbol: CreateChannel
visible_roles: [developer, test]
---

# 创建者入群会写入成员历史

成功保存创建者的 `ChannelMember` 后，系统调用 `ChannelMemberHistory().LogJoinEvent` 记录加入事件。
