---
id: eng.mattermost.channel.create.standard_flow
layer: L2
module: mattermost.channel
feature: channel_creation
status: draft
version: 1
derived_from:
  - eng.mattermost.channel.create.type_routing
  - eng.mattermost.channel.create.team_required
  - eng.mattermost.channel.create.team_limit
  - eng.mattermost.channel.create.creator_assignment
visible_roles: [developer, test, product]
---

# 标准团队频道创建规则

标准的团队频道创建入口面向公开/私有团队频道，不用于 Direct、Group、Board 或 Space。创建必须绑定团队，并受团队最大频道数量限制；通过用户创建入口时，当前用户会被记录为频道创建者。
