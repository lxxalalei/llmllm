---
id: product.mattermost.channel.create.managed_category
layer: L3
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
  - eng.mattermost.channel.create.feature_gates
visible_roles: [product, test, developer]
---

# 新频道的 Managed Category

当前实现表明，新建频道请求中即使带有 Managed Category，也只有在许可证与对应功能开关均满足时才会实际应用；不满足时系统忽略该设置。

> 状态为 `review`：许可证产品口径、管理端提示方式需要产品确认后才能发布。
