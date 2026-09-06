---
id: faq.mattermost.channel.membership.remove_cleanup
layer: L4
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- product.mattermost.channel.membership.remove_cleanup
behavior_rule_id: rule.mattermost.channel.membership.remove_cleanup
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- user
- product
- test
- developer
- admin
---

# 为什么我被移出频道后，相关线程状态也一起没了？

因为线程成员状态依赖你的频道成员身份。移除频道成员时，系统会同步清理这些依赖状态，并通知你的客户端和频道里的其他成员。
