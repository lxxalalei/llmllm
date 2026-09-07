---
id: product.mattermost.channel.creation.creator_membership
layer: L3
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.creator_membership.behavior
behavior_rule_id: rule.mattermost.channel.creation.creator_membership
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- product
- test
- developer
- admin
---

# 创建标准频道会建立创建者成员关系

创建标准团队频道成功后，创建者会立即成为该频道的成员并获得频道管理员身份；如果团队已经达到频道数量上限，创建会被拒绝。
