---
id: eng.mattermost.channel.create.default_category
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

# 创建完成后频道会加入创建者的默认分类

`CreateChannelWithUser` 在底层频道创建成功后调用 `addChannelToDefaultCategory`，将频道加入创建者的默认分类。
