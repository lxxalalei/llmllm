---
id: eng.mattermost.channel.archive_restore.archive_permission_and_default.fact
layer: L1
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: deleteChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: DeleteChannel
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- developer
- test
---

# 归档频道按类型校验删除权限且保护默认频道

`deleteChannel` 对 Open 要求 `delete_public_channel`，对 Private 要求 `delete_private_channel`；普通 API 只接受允许的频道类型。`DeleteChannel` 如果频道已经 archived 会拒绝；`town-square` 默认频道始终拒绝归档。
