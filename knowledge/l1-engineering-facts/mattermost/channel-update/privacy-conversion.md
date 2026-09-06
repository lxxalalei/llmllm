---
id: eng.mattermost.channel.update.privacy_conversion.fact
layer: L1
module: mattermost.channel
feature: channel_update
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: updateChannelPrivacy
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: UpdateChannelPrivacy
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: postChannelPrivacyMessage
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel_discoverable_visibility.go
  symbol: CancelPendingChannelJoinRequestsOnConvert
tags:
- mattermost
- channel
- channel_update
visible_roles:
- developer
- test
---

# 公开/私有转换使用专用权限并维护可发现申请状态

`updateChannelPrivacy` API 在转 Private 时要求 `convert_public_channel_to_private`，转 Open 时要求 `convert_private_channel_to_public`；默认频道不能转为 Private。App `UpdateChannelPrivacy` 拒绝 Space。Private→Open 时公开频道不再保留 Discoverable；更新后创建 privacy system post，若 post 失败则回滚类型（并恢复原 discoverable）。原先可发现的频道转 Open 成功后异步撤回 pending join requests。
