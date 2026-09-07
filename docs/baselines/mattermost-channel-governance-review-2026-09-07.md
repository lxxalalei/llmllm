# Mattermost Channel Knowledge Governance Review — 2026-09-07

## 目的

本次审计只处理第一版 Channel 知识基线中的知识治理问题，不重新设计编译框架，也不把“文件数量整齐”当质量目标。

审核原则：

- 一个 BehaviorRule 应对应一个稳定的业务 decision；
- 同一 decision 下的多个必要条件可以保留在一条 Rule 中；
- 同一动作成功后的状态变化、通知、hook 等生命周期副作用可以保留在一条 Rule 中；
- 不同频道类型、不同 actor/target、不同转换方向产生不同权限或结果时，应拆成独立 Rule；
- L4 按用户真实问题组织，可以引用 0/1/N 条 Rule，不要求与 Rule 数量一致。

## 审计结果

完整扫描当前 Channel Creation、Membership、Permission、Update / Privacy、Archive / Restore 的 BehaviorRule 后，确认 5 组粗粒度规则需要拆分；其余生命周期型和复合门禁型规则无需机械拆分。

### 1. Channel Creation

原 `create_permission_gate` 同时混合公开/私有权限、必要字段和标准入口类型边界，拆为：

- `create_open_permission`
- `create_private_permission`
- `standard_create_required_fields`
- `standard_create_type_boundary`

用户 FAQ “为什么能创建公开频道却不能创建私有频道”只关联公开/私有权限和标准入口类型边界，不为了数量对齐额外生成 FAQ。

### 2. Channel Membership

此前已将 `add_permission_split` 拆为：

- `open_self_add_permission`
- `open_add_other_permission`
- `private_add_permission`
- `direct_group_add_rejected`

本次继续将 `add_integrity_constraints` 拆为：

- `team_member_integrity`
- `member_add_type_boundary`
- `group_constrained_membership`
- `member_add_guarded_hook`

“管理员有权限加人但目标用户仍不能加入”的 FAQ 只关联团队成员完整性和群组约束两条 Rule。

### 3. Channel Permission

`base_scheme_invariant`、`manage_member_roles`、`moderation_scope_ceiling` 均保持不拆：它们分别对应单一 invariant/permission/ceiling decision，OR 条件或副作用没有形成新的独立业务决策。

### 4. Channel Update / Privacy

`property_permission_by_type` 拆为：

- `open_property_permission`
- `private_property_permission`
- `direct_group_limited_update`
- `unsupported_property_update_type`

`privacy_conversion` 按方向与对象边界拆为：

- `public_to_private_conversion`
- `private_to_public_conversion`
- `space_privacy_conversion_rejected`

每个转换方向仍保留自己的 state change、privacy system post、rollback；Private→Open 额外保留 discoverable 清理和 pending join request 撤回。

另外修复 `generic_update_guard_and_event`：BehaviorRule 现在显式保存 `ChannelWillBeUpdated` guarded hook，而不是只在 L2 文本中提到。

### 5. Channel Archive / Restore

`archive_permission_and_default` 拆为：

- `open_archive_permission`
- `private_archive_permission`
- `already_archived_rejected`
- `town_square_archive_rejected`
- `standard_archive_type_boundary`

Town Square FAQ 同时关联默认频道保护与公开/私有归档权限，但 `already_archived_rejected` 不因为同属 archive Feature 就被硬塞进该 FAQ。

另外修复 `restore_permission_and_guard`：BehaviorRule 现在显式保存 `ChannelWillBeRestored` guarded hook、非 Space 适用范围和 fail-closed 语义。

## 保持不拆的典型规则

以下规则字段较多，但仍属于单一业务行为，因此保留：

- `creation_side_effects`：一次创建成功后的分类、系统消息、WebSocket、plugin lifecycle；
- `add_lifecycle`：一次成员加入成功后的 history / hook / post / websocket；
- `remove_cleanup`：一次成员移除导致的 membership/thread cleanup 与通知；
- `discoverable_self_add`：一个完整的可发现私有频道 self-add 复合门禁；
- `archive_state_and_event` / `restore_state_and_event`：一次状态转换的持久化与事件生命周期。

## 当前发布边界

本次拆分后的新资产继续保持 `review`。原子化、Schema 合法、CI 通过都不等于业务知识已经可以 Published。

下一验收项是基于真实 Channel 用户问题执行 QA regression，检查：

1. 检索是否命中正确的 L4/L3，而不是旧粗粒度知识；
2. 同一问题需要多条 Rule 时是否能组合回答；
3. 权限、对象状态、actor/target、转换方向是否没有被混淆；
4. 无法回答的问题是否形成 Knowledge Gap，而不是从 Review 资产猜答案。
