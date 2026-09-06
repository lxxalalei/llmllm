# Mattermost 规模的成熟产品存量知识建库

- 状态：in_progress
- 路线：[Phase 4 — 成熟产品规模化知识构建](../roadmap.md)
- 所有者：Codex（实现与技术验收）
- 当前样板：Mattermost 完整 Channel 域

## 1. 目标

以 Mattermost 这类已经成熟、功能稳定、代码变化相对较少的大型 IM 产品作为规模样本，验证如何从大量已有源码建立可长期使用的企业产品知识库。

当前主要问题不是代码更新，而是：

1. 如何把业务域拆成可控 Feature；
2. 如何确定每个 Feature 需要读取的真实源码范围；
3. 如何从源码稳定抽出 L1 Engineering Facts；
4. 如何把最容易丢失的权限、条件、allow/deny、状态变化和副作用结构化；
5. 如何从同一语义事实生成开发、产品、普通用户三种知识视图；
6. 如何通过 QA Knowledge Gap 持续补库。

## 2. 非目标

当前阶段不投入主要资源做：

- 高频 Git commit / branch / webhook 跟踪；
- 全局行号同步；
- 复杂 revision identity、SHA 链或防伪链；
- 完整 Repository Graph / 全仓调用图；
- 为每条知识补大量测试；
- 默认运行 Mattermost 全量测试；
- Kafka、分布式任务集群或多机调度；
- 为了“未来可维护”提前建设复杂代码变化平台。

Phase 3 已实现的增量维护能力保留，但不作为成熟产品首次建库阻塞条件。

## 3. 当前主链路

```text
成熟产品源码
    ↓
Business Domain / Feature Scope
    ↓
真实源码 symbol
    ↓
L1 Engineering Facts
    ↓
BehaviorRule
    ├─ L2 Engineering View
    ├─ L3 Product View
    └─ L4 User View
    ↓
Semantic Review
    ↓
Canonical Knowledge
    ↓
Qdrant / QA
    ↓
Knowledge Gap
    ↓
继续补知识
```

## 4. 源码证据原则

SourceBinding 只有两个核心目标：

1. 防止模型伪造源码来源；
2. 后续人工核对时能回到真实代码。

核心证据：

```text
repo + file + symbol
```

例如：

```yaml
source:
  repo: mattermost/mattermost
  file: server/channels/app/channel.go
  symbol: addUserToChannel
```

程序负责确认文件和 symbol 真实存在，并把真实 symbol 源码交给模型。

`commit/revision` 和 `start_line/end_line` 仅作为可选辅助定位信息，不用于知识身份、首次建库门禁或全局同步。

## 5. 每层职责

### L1 — Engineering Facts

回答“代码实际上做了什么”。

重点：

- 权限检查；
- allow / deny；
- actor / target；
- 条件；
- 状态写入/删除；
- 特殊 bypass；
- 错误分支；
- system post；
- WebSocket / event；
- plugin hook；
- 业务相关副作用。

### BehaviorRule — 结构化业务事实

保存核心语义：

```text
actor
action
resource
conditions
decision
state_changes
side_effects
exceptions
evidence
```

BehaviorRule 不追求覆盖所有源码细节，只保存会影响业务规则、权限、状态或用户结果的内容。

### L2 — Engineering View

面向开发/测试，描述稳定工程规则。

### L3 — Product View

面向产品/测试/客服，描述谁在什么条件下可以做什么、拒绝规则、状态变化和例外。

### L4 — User View

面向普通员工，形成 FAQ、权限解释、错误原因、操作说明和常见场景。

## 6. Channel Membership 试点结论

早期真实模型运行证明：

```text
Code → L1 → L2
```

技术上可以运行，但连续文本抽象出现：

- L1 重复；
- L2 抽象不稳定；
- 条件范围扩大/缩小；
- unsupported ordering；
- self/other、allow/deny 等语义风险。

因此项目已经引入 BehaviorRule，并完成两条 Channel Membership 规则的最小语义验证：

- 成员移除生命周期；
- discoverable private channel self-add 限制。

结论：核心事实应先进入 BehaviorRule，再由同一规则生成 L2/L3/L4。

## 7. 当前实现状态

### 已完成：BehaviorRule Core

已经实现：

- BehaviorRule / conditions / state_changes / side_effects / exceptions；
- BehaviorRuleGenerator；
- OpenAI-compatible BehaviorRule Structured Output extractor；
- BehaviorRuleProjector；
- KnowledgeItem `behavior_rule_id`；
- 三层 view 默认 Draft；
- Channel Membership 语义测试。

### 已完成：BehaviorRule Scope Pipeline

`BatchKnowledgeScope` 支持：

```json
"pipeline": "behavior_rule"
```

新 pipeline 直接执行：

```text
Code
→ L1
→ BehaviorRule
→ L2/L3/L4
```

不再先调用旧的 L2 文本摘要生成器。

BehaviorRule pipeline 不允许 `auto_publish`。

### 已完成：完整 Channel Domain

当前五个 Feature：

```text
Channel Creation
Channel Membership
Channel Permission
Channel Update / Privacy
Channel Archive / Restore
```

配置：

```text
config/knowledge_scopes/mattermost-channel-creation.json
config/knowledge_scopes/mattermost-channel-membership.json
config/knowledge_scopes/mattermost-channel-permission.json
config/knowledge_scopes/mattermost-channel-update.json
config/knowledge_scopes/mattermost-channel-archive-restore.json
```

域 manifest：

```text
config/knowledge_domains/mattermost-channel.json
```

所有 Channel scope 均使用 `repo/file/symbol` 定位，不配置固定行号 range。

### 已完成：Domain Compiler

运行：

```bash
python scripts/compile_domain.py \
  /path/to/mattermost \
  config/knowledge_domains/mattermost-channel.json \
  --output-dir .scratch/channel-domain \
  --summary .scratch/channel-domain-summary.json
```

域级汇总至少包含：

```text
source_files
symbols
l1
behavior_rules
l2
l3
l4
```

## 8. 当前真正的下一步

不再做 Repository Graph 前置验证，也不再继续围绕 Channel Membership 做概念验证。

下一步直接是真实完整 Channel 域编译。

### Step 1 — Real Channel Compile

准备：

- 可读取的 Mattermost checkout；
- OpenAI-compatible 模型凭据。

执行完整 domain compiler。

目标产物：

```text
.scratch/channel-domain/
├─ channel_creation.json
├─ channel_membership.json
├─ channel_permission.json
├─ channel_update.json
└─ channel_archive_restore.json

.scratch/channel-domain-summary.json
```

### Step 2 — Semantic Review

重点检查：

- actor 是否正确；
- self / other 是否正确；
- allow / deny 是否反转；
- all / any 是否改变；
- 条件范围是否扩大/缩小；
- 权限是否遗漏；
- 状态变化是否遗漏；
- 副作用是否凭空增加；
- ordering 是否有真实证据；
- L2/L3/L4 是否仍表达 BehaviorRule 中同一事实。

不把 JSON 合法、ID 唯一等结构检查当成语义正确性证明。

### Step 3 — Channel Knowledge Coverage

形成真实覆盖报告：

```text
Feature                   Source   L1   Rules   L2   L3   L4   Review
Channel Creation          ...      ...  ...     ...  ...  ...  ...
Channel Membership        ...      ...  ...     ...  ...  ...  ...
Channel Permission        ...      ...  ...     ...  ...  ...  ...
Channel Update/Privacy    ...      ...  ...     ...  ...  ...  ...
Channel Archive/Restore   ...      ...  ...     ...  ...  ...  ...
```

覆盖率按业务 Feature 统计，不按代码行数统计。

### Step 4 — Publish

只有通过语义审核的知识进入 canonical Markdown / Qdrant。

模型成功生成不等于 Published。

### Step 5 — QA Validation

使用真实问题，例如：

- 为什么能看到私有频道却不能直接加入？
- 什么情况下可以邀请成员？
- 被移出频道后哪些状态会变化？
- 谁可以修改频道权限？
- 频道归档后还能恢复吗？
- 谁可以修改频道公开/私有属性？

无法回答的问题记录为 Knowledge Gap。

### Step 6 — Gap-driven Expansion

根据真实 Gap 决定下一业务域，而不是按代码目录机械扩展。

候选域：

- Team；
- User / Account；
- Post / Message；
- Roles / Permission；
- Notification；
- Search；
- File / Attachment；
- Call / Meeting。

## 9. 验收标准

一个 Feature 可进入正式知识库，至少满足：

1. repo/file/symbol 真实存在；
2. L1 没有明显 unsupported fact；
3. BehaviorRule 的关键条件和结果有 L1/源码证据；
4. allow/deny、actor、self/other、all/any 没有反转；
5. 关键状态变化和副作用没有明显遗漏；
6. L2 是工程规则，不是 L1 的机械复述；
7. L3/L4 不增加 BehaviorRule 不支持的新事实；
8. QA 能回答代表性真实问题；
9. 需要时可以追溯到真实源码。

不要求：

- 每条知识固定行号；
- 每条知识必须固定 commit；
- 为每条规则新增测试；
- 一次模型输出零错误；
- 全仓一次完成；
- 首次建库前完成 Repository Graph。

## 10. 决策记录

### 2026-09-06 — Mature Product First

当前产品形态是成熟大型 IM，代码变化不是主要矛盾。系统首先解决“已有代码如何变成高质量知识”，增量维护保持次要位置。

### 2026-09-06 — SourceBinding 只承担可追溯

核心源码身份使用 `repo + file + symbol`。revision/commit/line 是可选定位信息，不参与知识身份和首次建库门禁。

### 2026-09-06 — BehaviorRule 承接跨角色语义

L1 保存工程事实；BehaviorRule 保存关键业务条件和结果；L2/L3/L4 从同一规则生成。

### 2026-09-06 — 生成与发布分离

BehaviorRule pipeline 默认 Draft，禁止把生成成功直接视为正式发布。

### 2026-09-06 — Repository Graph 不再是当前前置条件

已有明确 Channel Feature scope 时直接开始建库。只有当 scope 维护成本成为真实问题时，再引入入口发现或调用图自动化。
