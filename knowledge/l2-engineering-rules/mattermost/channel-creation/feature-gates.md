---
id: eng.mattermost.channel.create.feature_gates
layer: L2
module: mattermost.channel
feature: channel_creation
status: draft
version: 1
derived_from:
  - eng.mattermost.channel.create.space_feature_flag
  - eng.mattermost.channel.create.managed_category_gate
visible_roles: [developer, test, product]
---

# 特殊频道能力受功能开关与许可证约束

Space 创建依赖 Docs 功能开关；Managed Category 同时依赖最低 Enterprise License 和对应 Feature Flag。调用方不能仅凭请求字段存在就假定这些能力会生效。
