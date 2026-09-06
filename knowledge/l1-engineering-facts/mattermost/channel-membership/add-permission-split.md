---
id: eng.mattermost.channel.membership.add_permission_split.fact
layer: L1
module: mattermost.channel
feature: channel_membership
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: addChannelMember
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 加入自己与添加他人使用不同权限

`addChannelMember` 对 Open 频道把“添加自己”和“添加他人”分开：self-add 依赖 `join_public_channels`，添加其他用户依赖 `manage_public_channel_members`。Private 频道要求 `manage_private_channel_members`。Direct/Group 被普通成员添加接口拒绝。
