---
id: eng.mattermost.channel.membership.discoverable_self_add.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.discoverable_self_add.fact
behavior_rule_id: rule.mattermost.channel.membership.discoverable_self_add
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 可发现私有频道的直接 self-add 会转入申请流程

可发现私有频道并不等于可以直接 self-add。没有 active policy 时，直接 self-add 被成员接口阻断，以加入申请流程承接；管理员添加其他用户不受这条 self-add 规则阻断。
