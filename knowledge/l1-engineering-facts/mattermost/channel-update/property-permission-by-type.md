---
id: eng.mattermost.channel.update.property_permission_by_type.fact
layer: L1
module: mattermost.channel
feature: channel_update
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: updateChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: patchChannel
tags:
- mattermost
- channel
- channel_update
visible_roles:
- developer
- test
---

# 频道属性修改权限随频道类型变化

`updateChannel` 对 Open 要求 `manage_public_channel_properties`，对 Private 要求 `manage_private_channel_properties`。Direct/Group 没有同类属性管理权限，因此只允许频道成员进入有限更新，并明确禁止修改 Name、DisplayName 或 Purpose；其他未知类型拒绝。
