---
id: faq.mattermost.channel.creation.team_channel_limit
layer: L4
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- product.mattermost.channel.creation.team_channel_limit
behavior_rule_ids:
- rule.mattermost.channel.creation.team_channel_limit
tags: [mattermost, channel, channel_creation]
visible_roles: [user, product, test, developer]
---

# 为什么我创建频道时提示"频道数量已达上限"？

每个团队允许创建的频道数量是有限的。当你的团队已经达到频道数量上限时，系统会阻止继续创建新频道。该上限由团队设置中的"频道数量上限"配置决定；达到上限后无法继续创建属于预期行为，可以联系管理员调整上限或清理不再使用的频道后再创建。
