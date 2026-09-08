---
id: product.mattermost.channel.creation.team_channel_limit
layer: L3
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.team_channel_limit.behavior
behavior_rule_id: rule.mattermost.channel.creation.team_channel_limit
tags: [mattermost, channel, channel_creation]
visible_roles: [product, test, developer]
---

# 团队频道数量上限

每个团队有允许创建的频道数量上限。当团队中的频道数已经达到上限时，用户不能再创建新频道，系统会给出"已达上限"的提示；上限值由团队设置中的频道数量上限配置决定。
