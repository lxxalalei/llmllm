---
id: eng.mattermost.channel.update.private_to_public_conversion.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.privacy_conversion.fact
behavior_rule_id: rule.mattermost.channel.update.private_to_public_conversion
tags: [mattermost, channel, channel_update]
visible_roles: [developer, test]
---

# 私有频道转公开会同步清理私有可发现状态

Private→Open 需要 `convert_private_channel_to_public`。公开频道不保留私有频道的 discoverable 状态；成功转换后写 privacy system post，并撤回原可发现频道仍待审批的加入请求；post 失败则回滚类型和 discoverable。
