---
id: eng.mattermost.channel.membership.add_integrity_constraints.fact
layer: L1
module: mattermost.channel
feature: channel_membership
status: review
version: 1
sources:
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: AddUserToChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/channel.go
  symbol: addUserToChannel
- repo: mattermost/mattermost
  ref: master
  file: server/channels/app/guarded_hooks.go
  symbol: runGuardedChannelMemberWillBeAdded
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 成员加入同时受团队、频道类型和群组约束

`AddUserToChannel` 默认要求目标用户存在有效 TeamMember；只有显式 `skipTeamMemberIntegrityCheck` 的内部路径可绕过。`addUserToChannel` 仅接受 Open、Private、Space；GroupConstrained 频道还会通过 `FilterNonGroupChannelMembers` 拒绝不满足群组约束的用户。保存前非 Space 频道还运行 ChannelMemberWillBeAdded guarded hook。
