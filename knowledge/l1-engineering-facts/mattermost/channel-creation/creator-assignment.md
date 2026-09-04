---
id: eng.mattermost.channel.create.creator_assignment
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

# 创建者 ID 在创建前写入频道

通过 `CreateChannelWithUser` 创建时，系统将传入的 `userID` 写入 `channel.CreatorId`，再调用 `CreateChannel(..., addMember=true)`。
