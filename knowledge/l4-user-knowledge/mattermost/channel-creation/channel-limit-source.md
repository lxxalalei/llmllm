---
id: faq.mattermost.channel.create.channel_limit_source
layer: L4
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
  - product.mattermost.channel.create.team_channel
visible_roles: [user, product, test, developer]
---

# 团队频道数量上限是由什么决定的？

上限由团队设置中的频道数量上限配置决定。创建时如果新增后超过该上限，系统会拒绝创建；达到上限后无法继续创建是预期行为。

> 已发布（2026-09-05）：对应 L3 产品逻辑（team_channel）已发布，本条 FAQ 对普通用户可见。
