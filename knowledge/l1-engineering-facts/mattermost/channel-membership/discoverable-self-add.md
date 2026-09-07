---
id: eng.mattermost.channel.membership.discoverable_self_add.fact
layer: L1
module: mattermost.channel
feature: channel_membership
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel_discoverable_visibility.go
  symbol: IsDiscoverableSelfAddBlocked
- repo: mattermost/mattermost
  ref: master
  file: server/channels/api4/channel.go
  symbol: addChannelMember
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 可发现私有频道的直接 self-add 会转入申请流程

`IsDiscoverableSelfAddBlocked` 在 Private + Discoverable + 非 PolicyEnforced + requester==target + DiscoverableChannels feature 开启时返回 true；`addChannelMember` 据此拒绝直接 POST。requester 添加其他用户时该规则不阻断。函数实现本身没有“尚未是成员”的判断。
