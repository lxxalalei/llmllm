---
id: product.conversation.work_order.auto_archive
layer: L3
module: conversation
feature: work_order
status: published
version: 1
derived_from:
  - eng.conversation.work_order.archive
visible_roles:
  - user
  - product
  - test
  - developer
---

# 工单会话自动归档

## 功能说明

已经结束且长期无活动的工单会话会自动进入归档状态。

## 触发条件

- 工单已经结束
- 连续一段时间没有新的有效消息

> 这里是示例知识，不代表真实产品规则。接入真实代码后必须由知识编译链和产品审核替换。

## 系统行为

- 会话从默认最近会话列表移出
- 历史消息仍然保留
- 用户可以通过归档入口查看
