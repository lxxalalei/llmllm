---
id: product.mattermost.channel.membership.add_integrity_constraints
layer: L3
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_integrity_constraints.behavior
behavior_rule_id: rule.mattermost.channel.membership.add_integrity_constraints
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

# 成员加入同时受团队、频道类型和群组约束

即使调用者有加人权限，目标用户仍必须满足频道本身的成员条件，例如团队成员资格和群组约束；系统内部有明确的 team-check bypass，但并不会取消所有其他门禁。
