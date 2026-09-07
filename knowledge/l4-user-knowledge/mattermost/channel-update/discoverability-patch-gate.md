---
id: faq.mattermost.channel.update.discoverability_patch_gate
layer: L4
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- product.mattermost.channel.update.discoverability_patch_gate
behavior_rule_id: rule.mattermost.channel.update.discoverability_patch_gate
tags:
- mattermost
- channel
- channel_update
visible_roles:
- user
- product
- test
- developer
- admin
---

# 为什么有些私有频道没有“可发现”开关，或者修改时报权限错误？

可发现性只适用于符合条件的私有频道。功能开关、共享频道状态以及你的可发现性管理权限都会影响是否能修改。
