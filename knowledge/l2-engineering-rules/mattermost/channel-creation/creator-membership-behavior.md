---
id: eng.mattermost.channel.creation.creator_membership.behavior
layer: L2
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.creator_membership.fact
behavior_rule_id: rule.mattermost.channel.creation.creator_membership
tags:
- mattermost
- channel
- channel_creation
visible_roles:
- developer
- test
---

# 创建标准频道会建立创建者成员关系

标准团队频道创建是“频道持久化 + 创建者管理员成员关系 + join history”的组合操作；团队频道数量上限在创建前门禁。
