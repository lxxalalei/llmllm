---
id: eng.mattermost.channel.creation.team_channel_limit.behavior
layer: L2
module: mattermost.channel
feature: channel_creation
status: review
version: 1
derived_from:
- eng.mattermost.channel.creation.team_channel_limit.fact
behavior_rule_id: rule.mattermost.channel.creation.team_channel_limit
tags: [mattermost, channel, channel_creation]
visible_roles: [developer, test]
---

# 团队频道数量上限校验规则

标准团队频道创建入口在落库前校验团队现有频道数：若新增后超过 `TeamSettings.MaxChannelsPerTeam` 配置值，返回 `api.channel.create_channel.max_channel_limit.app_error`（400），不创建频道。
