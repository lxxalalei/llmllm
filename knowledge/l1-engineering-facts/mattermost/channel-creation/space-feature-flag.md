---
id: eng.mattermost.channel.create.space_feature_flag
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

# Space 创建受 EnableDocs Feature Flag 控制

`CreateChannel` 遇到 Space 类型时会检查 `FeatureFlags.EnableDocs`；未启用时返回 Forbidden。
