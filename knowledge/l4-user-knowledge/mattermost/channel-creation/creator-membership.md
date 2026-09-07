---
id: faq.mattermost.channel.creation.creator_membership
layer: L4
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- product.mattermost.channel.creation.creator_membership
behavior_rule_id: rule.mattermost.channel.creation.creator_membership
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

# 创建频道后我会自动加入吗？

会。标准团队频道创建成功后，创建者会立即成为该频道成员，并获得频道管理员身份。团队达到频道数量上限时则无法继续创建。
