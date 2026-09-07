---
id: faq.mattermost.channel.create.public_private_channels
layer: L4
module: mattermost.channel
feature: channel_creation
status: review
version: 2
derived_from:
  - product.mattermost.channel.create.team_channel
  - product.mattermost.channel.creation.create_permission_gate
behavior_rule_ids:
  - rule.mattermost.channel.creation.create_permission_gate
visible_roles: [user, product, test, developer, admin]
---

# 公开频道和私有频道的创建规则一样吗？

不完全一样。标准创建入口都支持公开频道和私有频道，创建成功后的创建者成员初始化基本一致；但两种频道使用各自的创建权限门禁，能创建其中一种并不代表一定能创建另一种。
