---
id: eng.mattermost.channel.membership.add_integrity_constraints.behavior
layer: L2
module: mattermost.channel
feature: channel_membership
status: review
version: 1
derived_from:
- eng.mattermost.channel.membership.add_integrity_constraints.fact
behavior_rule_id: rule.mattermost.channel.membership.add_integrity_constraints
tags:
- mattermost
- channel
- channel_membership
visible_roles:
- developer
- test
---

# 成员加入同时受团队、频道类型和群组约束

真正落库前还有一组与 API 权限不同的完整性门禁：团队成员资格、频道类型、群组约束以及可拒绝/替换成员对象的插件 guard。内部 bypass 只针对 team membership check，不代表绕过其他约束。
