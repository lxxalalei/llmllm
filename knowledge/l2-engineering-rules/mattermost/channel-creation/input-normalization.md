---
id: eng.mattermost.channel.create.input_normalization_rule
layer: L2
module: mattermost.channel
feature: channel_creation
status: draft
version: 1
derived_from:
  - eng.mattermost.channel.create.input_normalization
visible_roles: [developer, test, product]
---

# 频道创建文本字段规范化规则

频道在持久化前会移除 DisplayName、DefaultCategoryName 和 ManagedCategoryName 两端空白。依赖这些字段进行比较或后续处理时，应以规范化后的值为准。
