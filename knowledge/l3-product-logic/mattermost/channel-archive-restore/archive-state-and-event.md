---
id: product.mattermost.channel.archive_restore.archive_state_and_event
layer: L3
module: mattermost.channel
feature: channel_archive_restore
status: review
version: 1
derived_from:
- eng.mattermost.channel.archive_restore.archive_state_and_event.behavior
behavior_rule_id: rule.mattermost.channel.archive_restore.archive_state_and_event
tags:
- mattermost
- channel
- channel_archive_restore
visible_roles:
- product
- test
- developer
- admin
---

# 归档写入 DeleteAt 并广播频道删除事件

频道归档成功后会进入已归档状态，并通知相关客户端。某些频道可被插件规则阻止归档；内部 Space backing channel 不产生标准聊天频道的归档提示。
