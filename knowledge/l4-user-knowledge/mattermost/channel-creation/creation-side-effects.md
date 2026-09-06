---
id: faq.mattermost.channel.creation.creation_side_effects
layer: L4
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- product.mattermost.channel.creation.creation_side_effects
behavior_rule_id: rule.mattermost.channel.creation.creation_side_effects
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- user
- product
- test
- developer
- admin
---

# 创建频道后为什么会立即出现在侧边栏并出现加入提示？

标准频道创建完成后，系统会同时更新创建者的频道分类、发送加入频道提示，并通知客户端有新频道，因此这些变化会紧接着创建操作出现。
