---
id: faq.mattermost.channel.create.creator_auto_join
layer: L4
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
  - product.mattermost.channel.create.team_channel
visible_roles: [user, product, test, developer]
---

# 为什么我创建频道后自动成为了频道成员？

通过标准创建入口创建频道时，创建者会自动加入新频道，并初始化相应的频道管理权限。

> 已发布（2026-09-05）：对应 L3 产品逻辑（team_channel）已发布，本条 FAQ 对普通用户可见。
