---
id: faq.mattermost.channel.update.privacy_conversion
layer: L4
module: mattermost.channel
feature: channel_update
status: review
version: 1
derived_from:
- product.mattermost.channel.update.privacy_conversion
behavior_rule_id: rule.mattermost.channel.update.privacy_conversion
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

# 为什么把私有频道转成公开后，待审批的加入申请消失了？

公开频道不再需要私有频道的加入申请流程。转换成功后，系统会撤回该频道仍在等待审批的加入请求。
