---
id: faq.mattermost.channel.create.public_private_channels
layer: L4
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
  - product.mattermost.channel.create.team_channel
visible_roles: [user, product, test, developer]
---

# 公开频道和私有频道的创建规则一样吗？

一样。标准创建入口同时支持公开与私有团队频道，创建后创建者都会自动成为成员并完成相同的成员初始化流程。

> 已发布（2026-09-05）：对应 L3 产品逻辑（team_channel）已发布，本条 FAQ 对普通用户可见。
