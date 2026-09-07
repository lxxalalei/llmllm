---
id: eng.mattermost.channel.permission.manage_member_roles.fact
layer: L1
module: mattermost.channel
feature: channel_permission
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: updateChannelMemberRoles
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: updateChannelMemberSchemeRoles
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- developer
- test
---

# 修改频道成员角色需要 manage_channel_roles

`updateChannelMemberRoles` 和 `updateChannelMemberSchemeRoles` 都是 session-required 路由，并在调用 App 前要求 requester 对目标频道拥有 `manage_channel_roles`。缺少该权限时直接拒绝。
