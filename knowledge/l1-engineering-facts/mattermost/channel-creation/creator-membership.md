---
id: eng.mattermost.channel.create.creator_membership
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

# addMember=true 时创建者会成为频道成员

`CreateChannel` 在 `addMember=true` 时读取创建者用户并保存 `ChannelMember`。成员记录使用默认通知设置，且 `SchemeAdmin=true`。
