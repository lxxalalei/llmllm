# Mattermost channel creation L4 preview review — 2026-09-08

这份报告是 `channel_creation` Feature 的 L4 用户意图预览，供后续编译器和人工审核使用。候选由人工与 Agent 整理；正文只把 BehaviorRule 作为事实证据，L3 仅用于核对血缘，**不是实际三阶段模型产出**。本轮没有调用模型，也没有修改、发布或退役任何 canonical knowledge。

## 本轮范围

预览收敛为 5 个有独立用户价值的意图：

| 意图 ID | 用户问题 | Rule | 处理计划 |
| --- | --- | --- | --- |
| `faq.mattermost.channel.creation.channel_limit` | 创建频道时提示数量已达上限，是什么意思？ | `rule.mattermost.channel.creation.team_channel_limit` | merge `faq.mattermost.channel.create.channel_limit_source`、`faq.mattermost.channel.create.limit`、`faq.mattermost.channel.creation.team_channel_limit` |
| `faq.mattermost.channel.creation.create_permission_gate` | 为什么我能创建公开频道，却不能创建私有频道？ | `rule.mattermost.channel.creation.create_open_permission`、`rule.mattermost.channel.creation.create_private_permission` | merge `faq.mattermost.channel.creation.create_permission_gate`、`faq.mattermost.channel.create.public_private_channels` |
| `faq.mattermost.channel.creation.creator_membership` | 创建频道后，我会自动成为成员和管理员吗？ | `rule.mattermost.channel.creation.creator_membership` | merge `faq.mattermost.channel.creation.creator_membership`、`faq.mattermost.channel.create.creator_auto_join` |
| `faq.mattermost.channel.creation.creation_side_effects` | 为什么新建频道会出现在侧边栏，并出现加入频道消息？ | `rule.mattermost.channel.creation.creation_side_effects` | merge `faq.mattermost.channel.creation.creation_side_effects`、`faq.mattermost.channel.create.default_category`、`faq.mattermost.channel.create.join_message` |
| `faq.mattermost.channel.creation.discoverable_private_creation` | 创建可发现的私有频道需要满足什么条件？ | `rule.mattermost.channel.creation.discoverable_private_creation` | 保留一个主题条目，merge 现有同 ID 条目 |

每条候选都是 L4 用户意图资产，不再按单个 Rule 机械生成一条 FAQ。公开/私有权限候选组合两条权限 Rule；其余候选各自组合一个足以支撑用户问题的 Rule。

## 内容边界

候选正文只保留现有 Rule 直接支持的判断：

- 频道上限只说明“创建后数量超过团队配置上限会被拒绝”和上限来自团队配置。正文没有写具体数值、设置界面、归档或删除是否释放额度。
- 公开/私有频道分别检查 `create_public_channel` 和 `create_private_channel`，并保留已登录与对应频道类型条件；不把一种权限扩展成另一种权限。
- 标准团队频道创建成功后，创建者成为成员，并以 `SchemeAdmin` 记录为频道管理员。这描述成功路径，不推断各阶段失败后的残留或回滚。
- 标准频道创建完成后，系统会把频道加入创建者默认频道分类、发布加入频道系统提示并发送客户端新频道事件。
- 可发现创建只覆盖私有频道、`discoverable_channels` 已启用、创建者拥有 `manage_private_channel_discoverability` 三项必要检查；这三项满足不代表其他频道创建条件都已通过。

正文没有写审查意见、证据缺口或未经 Rule 支撑的操作建议。具体缺口保存在预览 JSON 的 `plan.missing_evidence` 和 `review.missing_evidence` 中。

## QA 回归基线

`config/qa_regression/creation-l4-2026-09-08.json` 共包含 15 条题：10 条应由候选回答，5 条应在命中相关候选后标记 Knowledge Gap 并拒绝推断。这是本轮整理的回归集，不是来自真实用户流量的独立评测集。

缺口题覆盖：

1. 当前团队频道上限的具体数值；
2. 查看或修改频道上限的设置入口；
3. 归档频道是否释放可创建数量；
4. 启用 `discoverable_channels` 的具体界面入口；
5. 创建失败后是否留下成员关系：不能用成功路径反推所有失败或回滚行为。

这些题的 `expected_knowledge_id` 仍指向相关候选，`expected_gap` 为 `true`。因此验收目标是“检索命中后不编造答案”，不使用 BM25 未命中代替真实 QA 验收。每条题还包含必须保留的语义断言和禁止出现的结论。

## 审核决定

- 当前预览候选全部使用 `status: draft`，只允许进入 review 流程。
- `merge_ids` 只记录后续合并/替换计划；对已有治理目标 ID 的候选，`merge_ids` 明确包含现有目标本身和要合并的旧条目。本轮不修改旧 L4 文件，不改变其 published、review 或 deprecated 状态。
- 频道上限、创建者身份、可发现私有频道候选带有证据缺口。上限候选仍能回答“为什么被拒绝”，但不能回答具体数值、配置入口和额度释放方式；创建者身份候选未覆盖失败回滚；可发现候选不能提供启用 `discoverable_channels` 的界面入口。
- 若后续补齐操作文档或运行时配置数据，应为这些缺口另加有来源的知识，再更新对应 QA 题，不应扩写当前候选正文。

## 独立验收记录（2026-09-09）

主 Agent 核对六条 Rule、L1 源事实和对应 L3 血缘，并修正了失败路径反推、时间承诺及必要条件表述。五条候选均为 `draft`，`review.issues=[]` 仅表示本轮候选正文审阅未发现阻塞问题。

执行：

```bash
.venv/bin/python -m scripts.evaluate_l4 \
  docs/baselines/creation-l4-preview-2026-09-08.json \
  config/qa_regression/creation-l4-2026-09-08.json \
  --output /tmp/creation-l4-evaluation.json
```

结果退出码 0：5 个候选接纳、0 个拒绝；普通用户、正常模式、本地 BM25 的 `top_k=4` 下，15/15 道题命中目标，13/15 排名第一。`creation_private_permission_name` 排名第二，`creation_join_message` 排名第三；其余排名第一。实际退役旧 ID 无残留，沿用原 ID 的新正文不会误算成旧知识。

问答执行数为 0，15 道题的答案语义均仍待验收，其中 5 道是缺口题。上述结果证明候选组合与召回可运行，不证明真实问答正确率，也不证明模型生成的其他草稿有同等质量。真实 API 生成、真实 QA、HTTP 用户链路和 Qdrant 同步均未执行。

测试与边界记录见 [本轮实施验收](../plans/archive/creation-l4-user-intents.md)。
