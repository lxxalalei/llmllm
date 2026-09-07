---
id: eng.mattermost.channel.membership.remove_cleanup.fact
layer: L1
module: mattermost.channel
feature: channel_membership
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: removeChannelMembership
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: removeUserFromChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: postLeaveChannelMessage
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: postRemoveFromChannelMessage
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 移除成员会同步清理依赖状态并双路通知

`removeChannelMembership` 先移除 ChannelMember，再删除该用户在该频道的 ThreadMembership。`removeUserFromChannel` 随后记录 leave history、触发 `UserHasLeftChannel`，向频道和被移除用户分别发送 `user_removed`。本人退出发 leave system post，他人移除发 remove system post。默认频道中的非 Guest 用户不能被移除。
