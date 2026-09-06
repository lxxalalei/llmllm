---
id: eng.mattermost.channel.membership.add_lifecycle.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_lifecycle.fact
behavior_rule_id: rule.mattermost.channel.membership.add_lifecycle
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 成员加入成功后记录历史并同步多端状态

成员加入不是单一 SaveMember。成功加入包含 join history、缓存失效、插件生命周期、按 actor 区分的 system post，以及频道/目标用户双路实时通知。
