---
id: eng.mattermost.channel.creation.create_permission_gate.fact
layer: L1
module: mattermost.channel
feature: channel_creation
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: createChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: CreateChannelWithUser
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- developer
- test
---

# 公开/私有频道创建由对应权限门禁

`createChannel` 是会话登录接口。创建公开频道需要团队范围的 `create_public_channel` 权限；创建私有频道需要 `create_private_channel` 权限。请求必须提供 TeamId 和 DisplayName；Board/Space 不能通过普通 `/channels` 创建，`CreateChannelWithUser` 还拒绝 Direct/Group、Board 和 Space。
