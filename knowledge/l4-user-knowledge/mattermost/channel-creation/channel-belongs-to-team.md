---
id: faq.mattermost.channel.create.channel_belongs_to_team
layer: L4
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
  - product.mattermost.channel.create.team_channel
visible_roles: [user, product, test, developer]
---

# 创建频道时必须选择团队吗？

是的。标准入口创建的是某个团队下的频道，创建时必须指定所属团队；没有指定团队时，创建请求会被拒绝。

> 已发布（2026-09-05）：对应 L3 产品逻辑（team_channel）已发布，本条 FAQ 对普通用户可见。
