---
id: eng.mattermost.channel.membership.add_lifecycle.fact
layer: L1
module: mattermost.channel
feature: channel_membership
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: addUserToChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: AddChannelMember
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: PostAddToChannelMessage
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 成员加入成功后记录历史并同步多端状态

`addUserToChannel` 保存 ChannelMember 后记录 `LogJoinEvent` 并失效缓存。`AddChannelMember` 触发 `UserHasJoinedChannel` plugin hook；self/join 路径发 join system post，requester 添加他人时发 add-to-channel system post；同时分别向频道和被添加用户发送 `user_added` WebSocket。
