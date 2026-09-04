---
id: eng.mattermost.channel.create.input_normalization
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
    symbol: CreateChannel
visible_roles: [developer, test]
---

# 创建前会清理部分频道文本字段

`CreateChannel` 在持久化前对 `DisplayName`、`DefaultCategoryName`、`ManagedCategoryName` 执行 `strings.TrimSpace`。
