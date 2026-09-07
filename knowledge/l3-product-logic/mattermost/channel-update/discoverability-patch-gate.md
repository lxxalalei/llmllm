---
id: product.mattermost.channel.update.discoverability_patch_gate
layer: L3
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.discoverability_patch_gate.behavior
behavior_rule_id: rule.mattermost.channel.update.discoverability_patch_gate
tags:
- mattermost
- channel
- channel_update
visible_roles:
- product
- test
- developer
- admin
---

# 私有频道可发现性修改受类型、共享状态和权限限制

只有符合条件的私有频道才能修改“可发现”状态；共享频道和普通公开频道不能按这条路径切换可发现性。
