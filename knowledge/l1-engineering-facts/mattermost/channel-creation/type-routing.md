---
id: eng.mattermost.channel.create.type_routing
layer: L1
module: mattermost.channel
feature: channel_creation
status: draft
version: 1
sources:
  - repo: mattermost/mattermost
    ref: master
    commit: 43b2ae87e06b06abe01f9382ec26899c54c31728
    file: server/channels/app/channel.go
    symbol: CreateChannelWithUser
visible_roles: [developer, test]
---

# 频道创建入口限制频道类型

`CreateChannelWithUser` 拒绝 Direct、Group、Board 和 Space 类型。普通公开/私有团队频道走该入口；Board 和 Space 使用其他创建路径。
