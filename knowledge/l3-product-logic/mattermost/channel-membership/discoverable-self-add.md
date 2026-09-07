---
id: product.mattermost.channel.membership.discoverable_self_add
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.discoverable_self_add.behavior
behavior_rule_id: rule.mattermost.channel.membership.discoverable_self_add
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- product
- test
- developer
- admin
---

# 可发现私有频道的直接 self-add 会转入申请流程

用户能看到某个可发现私有频道时，仍可能不能直接加入。对于没有策略自动判定的可发现私有频道，自助加入需要走申请流程；管理员邀请其他用户属于不同路径。
