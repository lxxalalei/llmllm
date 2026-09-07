---
id: product.mattermost.channel.membership.add_lifecycle
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_lifecycle.behavior
behavior_rule_id: rule.mattermost.channel.membership.add_lifecycle
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

# 成员加入成功后记录历史并同步多端状态

成员加入成功后，系统会同步更新历史、客户端成员状态和频道内提示；自己加入与被他人添加时，频道里的系统提示语义不同。
