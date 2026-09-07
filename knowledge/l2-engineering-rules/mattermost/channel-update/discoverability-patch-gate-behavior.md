---
id: eng.mattermost.channel.update.discoverability_patch_gate.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.discoverability_patch_gate.fact
behavior_rule_id: rule.mattermost.channel.update.discoverability_patch_gate
tags:
- mattermost
- channel
- channel_update
visible_roles:
- developer
- test
---

# 私有频道可发现性修改受类型、共享状态和权限限制

可发现性是私有频道的受控属性。更新时必须满足功能开关、私有类型、非 shared 和专门的可发现性管理权限。
