---
id: product.mattermost.channel.membership.remove_cleanup
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.remove_cleanup.behavior
behavior_rule_id: rule.mattermost.channel.membership.remove_cleanup
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

# 移除成员会同步清理依赖状态并双路通知

用户退出或被移出频道后，其频道成员身份和依赖该身份的线程成员状态会一起失效。系统还会根据“自己离开”还是“被别人移除”显示不同系统提示。非访客用户不能从默认频道移除。
