---
id: eng.mattermost.channel.permission.base_scheme_invariant.fact
layer: L1
module: mattermost.channel
feature: channel_permission
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: UpdateChannelMemberRoles
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: updateChannelMemberRolesInternal
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- developer
- test
---

# 常规角色更新必须保留成员基础 Scheme 身份

`UpdateChannelMemberRoles` 调用内部实现时 `allowSchemeUserUnset=false`。内部实现解析角色后，如果成员同时 `SchemeGuest=false` 且 `SchemeUser=false`，常规 API/plugin 路径返回 Bad Request；只有 bulk import 内部路径可以临时设置 `allowSchemeUserUnset=true` 跳过该检查。
