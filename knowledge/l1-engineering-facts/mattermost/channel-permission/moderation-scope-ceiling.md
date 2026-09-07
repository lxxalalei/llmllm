---
id: eng.mattermost.channel.permission.moderation_scope_ceiling.fact
layer: L1
module: mattermost.channel
feature: channel_permission
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: PatchChannelModerationsForChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: GetChannelModerationsForChannel
tags:
- mattermost
- channel
- channel_permission
visible_roles:
- developer
- test
---

# 频道 moderation 不能授予高于上级角色的权限

`PatchChannelModerationsForChannel` 先取得 team/higher-scoped member/guest permissions。若 patch 尝试给 Members 或 Guests 开启上级角色本身没有的 permission，会返回 Forbidden。频道定制权限与上级完全一致时，代码会删除频道专用 scheme 并回落到上级角色；scheme 创建/删除会发送 `channel_scheme_updated`。
