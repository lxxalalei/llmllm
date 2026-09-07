# Mattermost Channel 全域知识基线 — 2026-09-07

## 结论

第一版完整 Channel 主域知识基线已经形成，五个 Feature 均有真实源码证据、L1、BehaviorRule 和三种角色视图。

本轮新增基线资产：

| Feature | L1 | BehaviorRule | L2 | L3 | L4 |
|---|---:|---:|---:|---:|---:|
| Channel Creation | 4 | 4 | 4 | 4 | 4 |
| Channel Membership | 5 | 5 | 5 | 5 | 5 |
| Channel Permission | 3 | 3 | 3 | 3 | 3 |
| Channel Update / Privacy | 4 | 4 | 4 | 4 | 4 |
| Channel Archive / Restore | 4 | 4 | 4 | 4 | 4 |
| **合计** | **20** | **20** | **20** | **20** | **20** |

全部新资产状态为 `review`。这表示源码语义核查已经完成，但尚未经过真实 QA 与正式发布切换。

旧 Channel Creation Published 资产暂时保留，避免新基线尚未 QA 时影响当前 Serve Plane。后续新基线通过 QA 后再决定旧资产 deprecated/outdated/published 切换。

## 已覆盖主题

### Channel Creation

- Open / Private 创建权限分流；
- 标准频道创建入口和 Direct / Group / Board / Space 边界；
- Discoverable Private 创建门禁；
- 创建者自动成为管理员成员并记录 join history；
- 默认分类、system post、WebSocket、plugin lifecycle。

### Channel Membership

- Open self-add 与 add-others 权限差异；
- Private 成员管理权限；
- team membership integrity 与显式内部 bypass；
- Open / Private / Space 类型边界；
- group-constrained membership；
- guarded member-add；
- discoverable private direct self-add 申请流门禁；
- join history、system post、双路 `user_added`；
- 移除时 ChannelMember + ThreadMembership 清理、leave history、双路 `user_removed`；
- Town Square 非 Guest 不可移除。

### Channel Permission

- `manage_channel_roles` 成员角色管理门禁；
- 常规角色修改必须保留 SchemeUser / SchemeGuest 基础身份；
- bulk import 两阶段内部例外；
- moderation 不能突破 higher-scoped role 权限上限；
- 频道 scheme 恢复继承及 `channel_scheme_updated`。

### Channel Update / Privacy

- Open / Private 属性管理权限；
- Direct / Group 有限字段更新；
- archived channel / generic type mutation 拒绝；
- `ChannelWillBeUpdated` guarded hook；
- `channel_updated` 客户端同步；
- Discoverable 修改的 feature/type/shared/permission 门禁；
- Open/Private 转换专用权限；
- Town Square / Space 转换边界；
- privacy system post、失败回滚；
- discoverable private → open 后 pending join request 撤回。

### Channel Archive / Restore

- Open / Private 归档权限；
- Town Square 不可归档；
- soft delete `DeleteAt`；
- `ChannelWillBeArchived` 可拒绝；
- `channel_deleted`；
- restore 的 manage_team / system channel admin 权限；
- 已归档状态前置条件；
- `ChannelWillBeRestored` guarded hook；
- `DeleteAt=0` + `channel_restored`；
- Space backing channel 的聊天生命周期例外。

## Semantic Review 结果

本轮人工模型审核重点检查了 condition、actor、allow/deny、state change、side effect 和 exception。

已明确处理：

1. `IsDiscoverableSelfAddBlocked` 的源码注释提到“尚未是成员”，但函数实现本身没有该判断，因此没有把这个条件写进 BehaviorRule。
2. 早期 Channel Membership 基准曾误认为普通 join 不记录历史；当前源码确认 SaveMember 后会记录 `LogJoinEvent`，新基线已按真实行为写入。
3. 不声明没有源码支撑的 plugin hook 精确全局顺序；只记录能够直接确认的前置/后置语义和 guard fail mode。
4. L2/L3/L4 不再逐层改写事实，均与对应 BehaviorRule 绑定。

## 已知缺口

第一版“完整 Channel 主域”表示五个核心 Feature 均已建立业务规则基线，不表示 Channel 目录下所有代码路径已经穷尽。

当前明确保留的缺口：

1. **ABAC membership policy 细节**：`channel_join_request.go` 注释声称 `AddChannelMember/addUserToChannel` 会再次执行 PDP，但当前主 `channel.go` 核查未找到同名显式 `evaluateChannelMembership` 调用。暂不把该注释升级为正式 BehaviorRule，后续应单独核清真实调用路径。
2. **Join Request 完整生命周期**：本轮覆盖“discoverable private direct self-add 必须走申请”的入口规则，但没有完整结构化 request / withdraw / approve / deny / reviewer queue。
3. **Permanent Delete**：归档/恢复基线聚焦软删除；永久删除 posts/members/policies 等深度清理尚未展开。
4. **Shared Channel remote sync**：成员、归档等操作的远端集群同步副作用未完整结构化。
5. **次要 Update 能力**：AutoTranslation、Managed Category 等专用字段路径没有全部做 BehaviorRule。
6. **成员偏好设置**：notification props / autotranslation 等成员级配置未进入 Channel Permission 基线。

这些缺口应由后续真实 QA 与使用频率决定优先级，而不是现在无边界扩代码范围。

## QA 验收问题集合

下一阶段至少使用以下真实问题验证检索和回答：

- 为什么我能加入公开频道，却不能把别人加入？
- 为什么能看到私有频道却不能直接加入？
- 为什么管理员有加人权限仍可能加不进去？
- 被移出频道后为什么线程状态也消失？
- 为什么 Town Square 的成员不能被正常移除？
- 为什么我能管理频道内容却不能设频道管理员？
- 为什么某个频道权限开关不能打开？
- 为什么私聊/群聊不能像普通频道一样改名称或用途？
- 为什么编辑频道不能直接把公开频道改成私有？
- 为什么某些私有频道不能开启可发现？
- 为什么私有频道转公开后待审批加入申请消失？
- 为什么 Town Square 不能归档？
- 频道归档是不是永久删除？
- 谁可以恢复归档频道？
- 恢复频道后为什么客户端会自动重新显示？

## 下一步

1. CI 校验 YAML BehaviorRule、L1 evidence ID 和三角色视图关系；
2. 将本基线加载到检索测试环境；
3. 用上述 QA 集合执行真实问答；
4. 根据错误答案和 `knowledge_gap` 修订/补充规则；
5. 通过 QA 的资产再从 `review` 进入 `published`，并决定旧 Creation 资产的替换策略。
