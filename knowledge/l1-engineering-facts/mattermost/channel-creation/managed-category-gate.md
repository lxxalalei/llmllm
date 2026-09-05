---
id: eng.mattermost.channel.create.managed_category_gate
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

# Managed Category 需要许可证与 Feature Flag

若创建请求带有 `ManagedCategoryName`，只有满足最低 Enterprise License 且 `FeatureFlags.ManagedChannelCategories` 开启时才尝试设置；否则该值被忽略并清空。
