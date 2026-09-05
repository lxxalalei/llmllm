---
id: faq.mattermost.channel.create.default_category
layer: L4
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
  - product.mattermost.channel.create.team_channel
visible_roles: [user, product, test, developer]
---

# 新建频道为什么会出现在我的默认频道分类里？

标准创建流程会在频道创建成功后，把新频道加入创建者的默认频道分类。

> 已发布（2026-09-05）：对应 L3 产品逻辑（team_channel）已发布，本条 FAQ 对普通用户可见。
