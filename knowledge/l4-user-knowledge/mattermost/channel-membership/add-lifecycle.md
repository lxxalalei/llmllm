---
id: faq.mattermost.channel.membership.add_lifecycle
layer: L4
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- product.mattermost.channel.membership.add_lifecycle
behavior_rule_id: rule.mattermost.channel.membership.add_lifecycle
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

# 为什么有人加入频道时会出现不同的系统提示？

系统会区分“用户自己加入”和“由其他人添加”。两种路径都会建立成员状态并通知客户端，但频道中的系统提示会根据实际操作者不同而变化。
