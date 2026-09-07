---
id: faq.mattermost.channel.create.space_unavailable
layer: L4
module: mattermost.channel
feature: channel_creation
status: draft
version: 1
derived_from:
  - product.mattermost.channel.create.space_availability
visible_roles: [user, product, test, developer]
---

# 为什么我不能创建 Space？

Space 依赖 Docs 功能能力，并且不使用普通团队频道的标准创建入口。相关能力未开启时，Space 创建会被拒绝。
