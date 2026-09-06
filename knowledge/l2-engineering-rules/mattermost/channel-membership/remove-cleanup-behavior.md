---
id: eng.mattermost.channel.membership.remove_cleanup.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.remove_cleanup.fact
behavior_rule_id: rule.mattermost.channel.membership.remove_cleanup
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 移除成员会同步清理依赖状态并双路通知

成员移除是复合清理，不是只删一条 ChannelMember。依赖的线程成员状态、历史和客户端通知都随之处理；默认频道对非 Guest 有额外不可移除规则。
