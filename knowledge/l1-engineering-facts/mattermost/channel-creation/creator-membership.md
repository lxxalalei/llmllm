---
id: eng.mattermost.channel.creation.creator_membership.fact
layer: L1
module: mattermost.channel
feature: channel_creation
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: CreateChannelWithUser
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: CreateChannel
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- developer
- test
---

# 创建标准频道会建立创建者成员关系

`CreateChannelWithUser` 先检查团队频道数量上限并把 `CreatorId` 设为当前用户。`CreateChannel(addMember=true)` 保存频道后创建该用户的 ChannelMember，设置 `SchemeAdmin=true`，按 guest 状态设置 SchemeGuest/SchemeUser，并记录 ChannelMemberHistory join event。
