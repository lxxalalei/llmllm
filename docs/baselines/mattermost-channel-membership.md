# Mattermost Channel Membership 人工知识基准

- 状态：manual baseline
- 上游仓库：`mattermost/mattermost`
- 检查 commit：`b3946ef5e2b85a27d365af2592cf1262de6a665e`
- Feature：`mattermost.channel / channel_membership`
- 用途：作为 Batch Knowledge Compiler 首次真实运行的对照答案，不直接发布为 canonical knowledge。

## 1. 边界

本基准关注普通 Channel Membership 的“加入 / 邀请 / 移除 / 离开”主链：

```text
HTTP API
→ Channel app layer
→ membership gate / guard
→ ChannelMember persistence
→ side effects
→ removal cleanup
```

当前 scope：

- `server/channels/api4/channel.go`
  - `addChannelMember`
  - `removeChannelMember`
- `server/channels/app/channel.go`
  - `addUserToChannel`
  - `AddUserToChannel`
  - `AddChannelMember`
  - `removeUserFromChannel`
  - `removeChannelMembership`
  - `PostAddToChannelMessage`
  - `postLeaveChannelMessage`
  - `postRemoveFromChannelMessage`
- `server/channels/app/guarded_hooks.go`
  - `runGuardedChannelMemberWillBeAdded`
- `server/channels/app/channel_discoverable_visibility.go`
  - `IsDiscoverableSelfAddBlocked`

相关但暂不并入本 Feature 的路径：

- `channel_join_request.go`：请求加入、审核与 ABAC fast path，作为相邻 Feature/扩展证据；
- `syncables.go`、shared-channel service：内部同步调用方，用于确认 `SkipTeamMemberIntegrityCheck` 的例外语义；
- SQL Store 具体实现：本轮只在 App 行为需要确认时下钻，不把 SQL 细节本身当产品知识；
- Web 前端：本轮以服务端事实为主。

## 2. L1 概念基准

以下不是最终 Knowledge ID，而是模型输出必须覆盖或正确处理的概念清单。

### 加入入口与权限

1. `/channels/{channel_id}/members` 的 POST 由 `addChannelMember` 处理，并要求登录会话。
2. API 层不允许通过普通 Channel Member endpoint 给 Direct / Group channel 增加成员。
3. Private channel 的成员管理受 `manage_private_channel_members` 权限控制；Public channel 使用对应的 public member-management permission。
4. Discoverable private channel 存在特殊的 self-add 规则：满足阻断条件时，用户不能直接把自己加入频道，而必须进入 join-request/approval 流程。
5. `IsDiscoverableSelfAddBlocked` 只阻断“private + discoverable + 无 active policy + requester == target + feature flag 开启”的 self-add；管理员邀请别人不受这条阻断。

### App 层成员加入

6. `AddChannelMember` 是更高层的成员加入入口，会读取目标用户并拒绝已删除用户。
7. `ChannelMemberOpts.UserRequestorID` 用于保留邀请/操作发起者身份；设置后会解析对应 requestor user。
8. `ChannelMemberOpts.PostRootID` 会沿成员加入流程传给 add-to-channel 系统消息，用于把用户可见的加入提示关联到指定 root post。
9. `AddUserToChannel` 默认要求目标用户是对应 Team 的有效成员；`SkipTeamMemberIntegrityCheck` 是显式内部例外。
10. 如果 TeamMember 已被删除/失效，普通加入路径会拒绝继续加入 Channel。
11. `addUserToChannel` 的 app 层成员类型边界是 Open / Private / Space；其他 Channel type 被拒绝。
12. Group-constrained channel/team 会进一步限制可加入用户；不满足约束时返回 `api.channel.add_members.user_denied`。

### Guard / policy

13. 非 Space channel 在保存新成员前会执行 `runGuardedChannelMemberWillBeAdded`。
14. `ChannelMemberWillBeAdded` hook 可以拒绝本次加入，也可以返回 replacement ChannelMember 修改待保存成员。
15. 对声明为 channel guard 的 plugin，plugin system disabled、guard plugin inactive 或 guard RPC failure 都按 fail-closed 处理，不继续保存成员。
16. 没有实现该 hook 的 guard claimant 被视为“无意见”，不会因为返回空值而自动拒绝。

### 加入后的可观察行为

17. 成员成功加入后会产生 `user_added` WebSocket 事件，使频道/目标用户侧能够刷新成员状态。
18. 当存在明确 requestor 时，加入流程会异步生成 AddToChannel system post；该消息区分被加入者与操作发起者。
19. 成员加入完成后会触发 plugin 的 `UserHasJoinedChannel` 生命周期通知；邀请场景可携带 actor/requestor 语义。
20. 不应凭“成员加入”这一概念自动断言普通 `AddChannelMember/AddUserToChannel` 会调用 `ChannelMemberHistory.LogJoinEvent`：在本次源码检查中，显式 `LogJoinEvent` 命中集中在默认频道、频道创建、导入等其他路径。本条是反幻觉检查，不是对整个仓库“永远不记录 join history”的全局断言。

### 移除与离开

21. `removeChannelMembership` 先删除 ChannelMember，并继续删除该用户在该 channel 下的 ThreadMemberships；源码注释明确要求这两类状态一起清理。
22. `removeUserFromChannel` 在成员移除后记录 `ChannelMemberHistory.LogLeaveEvent`。
23. 成员被移除后会广播 `user_removed`；由于被移除用户已不再属于该频道，还会额外向该用户发送定向的 removal event。
24. 成员移除后会异步触发 `UserHasLeftChannel` plugin hook；由他人移除时可保留 actor 语义。
25. 用户主动离开与被他人/系统移除会生成不同的 system post：前者走 `postLeaveChannelMessage`，后者走 `postRemoveFromChannelMessage`。

## 3. L2 规则基准

模型不要求逐字输出以下句子，但工程规则应该覆盖这些语义，而且必须能追溯到对应 L1。

1. **Channel membership 是多层门控行为。** HTTP permission、Team membership、group constraint、discoverable/ABAC 规则和 plugin guard 都可能在持久化前拒绝成员加入。
2. **Team membership 是普通 Channel membership 的前置完整性约束。** 绕过该检查必须由内部调用方显式选择，并由调用方负责先满足上游成员关系。
3. **Group-constrained membership 不是普通邀请权限的替代品。** 即使调用方能够执行成员管理，目标用户仍可能因为 group constraint 被拒绝。
4. **Discoverable private self-join 与管理员邀请是不同路径。** 无 active policy 的 discoverable private channel 可以要求 self-add 进入审批，但不能因此阻断管理员/审核人添加其他用户。
5. **Channel guard 在成员写入前拥有 veto / replacement 能力。** 对已声明 guard 的频道，guard 基础设施故障采用 fail-closed；普通未声明 guard 的 hook 保持原有非 guard 行为。
6. **成员加入不是单纯写一行 ChannelMember。** 成功路径还承担 WebSocket、系统消息和 plugin lifecycle 等可观察副作用，因此绕过 App 层直接写 Store 不等价于完整业务加入流程。
7. **成员移除包含依赖状态清理。** 撤销 ChannelMember 时还必须清理该频道的 ThreadMemberships，避免用户已失去频道访问但线程关注状态仍残留。
8. **成员移除的通知需要覆盖频道内其他成员和被移除用户本人。** 被移除用户无法再依赖频道广播，因此存在额外的定向 removal event。
9. **actor/requestor 是 membership 生命周期的一部分。** 邀请、审核通过、自主离开、被移除等不同来源会影响 system post 和 plugin hook 的语义。

## 4. 模型结果验收

真实 `compile_scope.py` 运行后按以下标准与本基准比较：

- Core concept coverage：上述 L1 核心概念应高覆盖；遗漏必须能指出对应源码范围是否未被送入模型。
- Unsupported fact：0。不能把注释、测试名称或常识扩写成源码没有支持的事实。
- SourceBinding：repo / commit / file / symbol / line 必须全部绑定到真实 source。
- Wrong attribution：0。不能把 API permission 规则错误绑定到 App persistence symbol，反之亦然。
- Duplicate fact：同一条件/副作用不要因为多入口重复生成多条近义事实。
- L2 dependency：每条 L2 `derived_from` 必须来自本次生成的 L1，不能从模型记忆补规则。
- L2 abstraction：规则可以跨多个 L1 综合，但不能升级成未经代码支持的产品意图或安全承诺。
- Negative check：如果模型声称普通 AddChannelMember 明确记录 join history，必须给出本 scope 中的直接代码证据，否则判为 unsupported。

## 5. 下一步

1. 用当前 scope 在真实 Mattermost checkout 上运行 Batch Compiler。
2. 保存原始 L1/L2 preview，不直接 publish。
3. 对照本基准标记 covered / missed / unsupported / duplicate / wrong-binding。
4. 如果遗漏来自 scope 不完整，先扩 source scope；如果 scope 已包含证据但模型仍漏，再调整 extractor prompt/上下文组织。
5. 只有知识质量稳定后才进入正式 Review / Publish / Qdrant / QA 验证。
