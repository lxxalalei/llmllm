---
id: eng.mattermost.channel.create.creator_membership_rule
layer: L2
module: mattermost.channel
feature: channel_creation
status: draft
version: 1
derived_from:
  - eng.mattermost.channel.create.creator_membership
  - eng.mattermost.channel.create.join_history
  - eng.mattermost.channel.create.default_category
  - eng.mattermost.channel.create.join_message
  - eng.mattermost.channel.create.websocket_event
visible_roles: [developer, test, product]
---

# 频道创建者成员初始化规则

用户通过标准入口创建频道时，系统不仅持久化频道，还会初始化创建者的成员关系：保存成员记录并赋予频道管理员标记、记录加入历史、加入默认分类、发布加入系统消息，并发送频道创建 WebSocket 事件。
