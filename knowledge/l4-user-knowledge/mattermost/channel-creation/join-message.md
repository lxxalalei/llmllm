---
id: faq.mattermost.channel.create.join_message
layer: L4
module: mattermost.channel
feature: channel_creation
status: published
version: 1
derived_from:
  - product.mattermost.channel.create.team_channel
visible_roles: [user, product, test, developer]
---

# 为什么新建频道后会出现加入频道的系统消息？

当前标准创建流程会在频道建立后，为创建者记录并发布加入频道的系统消息。

> 已发布（2026-09-05）：对应 L3 产品逻辑（team_channel）已发布，本条 FAQ 对普通用户可见。
