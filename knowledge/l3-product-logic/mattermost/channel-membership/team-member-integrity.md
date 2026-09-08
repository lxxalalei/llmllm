---
id: product.mattermost.channel.membership.team_member_integrity
layer: L3
module: mattermost.channel
feature: channel_membership
status: published
version: 1
derived_from:
- eng.mattermost.channel.membership.team_member_integrity.behavior
behavior_rule_id: rule.mattermost.channel.membership.team_member_integrity
tags: [mattermost, channel, channel_membership]
visible_roles: [product, test, developer, admin]
---

# 加入频道通常要求先属于对应团队

普通成员添加不仅看“谁有权加人”，目标用户还需要具备有效团队成员关系；内部特殊流程可以显式跳过这一项，但不是普通用户路径。
