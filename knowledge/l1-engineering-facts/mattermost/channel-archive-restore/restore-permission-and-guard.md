---
id: eng.mattermost.channel.archive_restore.restore_permission_and_guard.fact
layer: L1
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: restoreChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: RestoreChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/guarded_hooks.go
  symbol: runGuardedChannelWillBeRestored
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- developer
- test
---

# 恢复归档频道需要团队管理或系统频道管理权限

`restoreChannel` 是 session-required 路由。API 要求 requester 对团队拥有 `manage_team`，或拥有系统控制台频道管理权限 `sysconsole_write_user_management_channels`。`RestoreChannel` 要求目标当前 `DeleteAt != 0`；非 Space 还运行 `ChannelWillBeRestored` guarded hook，guard 不可用/RPC 错误时 fail-closed，插件可拒绝恢复。
