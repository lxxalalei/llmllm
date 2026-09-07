---
id: product.mattermost.channel.membership.group_constrained_membership
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.group_constrained_membership.behavior
behavior_rule_id: rule.mattermost.channel.membership.group_constrained_membership
tags: [mattermost, channel, channel_membership]
visible_roles: [product, test, developer, admin]
---

# 受群组约束的频道还要求目标用户满足群组条件

GroupConstrained 频道的成员资格是一道独立业务门禁。即使操作者有加人权限、目标用户也属于团队，只要群组条件不满足仍会被拒绝。
