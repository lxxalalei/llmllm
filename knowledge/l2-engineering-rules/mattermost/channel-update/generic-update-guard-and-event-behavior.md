---
id: eng.mattermost.channel.update.generic_update_guard_and_event.behavior
layer: L2
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- eng.mattermost.channel.update.generic_update_guard_and_event.fact
behavior_rule_id: rule.mattermost.channel.update.generic_update_guard_and_event
tags:
- mattermost
- channel
- channel_update
visible_roles:
- developer
- test
---

# 通用更新禁止归档频道改类型，并经过插件 guard

通用更新把“频道类型变化”排除在普通属性更新之外，并允许插件在写入前拒绝/替换更新内容；guarded channel 对 guard 失效采取 fail-closed。成功更新通过 `channel_updated` 同步客户端，Space 是例外。
