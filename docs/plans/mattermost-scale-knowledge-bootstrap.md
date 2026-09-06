# Mattermost 规模的成熟产品存量知识建库

- 状态：in_progress
- 路线：[Phase 4 — 规模化知识构建](../roadmap.md#phase-4--规模化知识构建-in_progress)
- 所有者：Codex（实现与技术验收）
- 依赖：现有 Repository Inventory、KnowledgeItem/SourceBinding、发布与检索链路；固定 Mattermost 基线 `b3946ef5e2b85a27d365af2592cf1262de6a665e`

## 目标与非目标

### 目标

以 Mattermost 这类成熟存量产品为规模基准，将当前“人工圈定 Feature 后整批调用模型”的知识构建方式，改造成可全仓发现、按业务入口切片、可断点续跑且能够量化覆盖率的存量知识编译系统。

首轮建库的核心结果不是覆盖每一行代码，而是覆盖可发现的产品行为入口、权限与拒绝门禁、状态转换、持久化影响和外部可见副作用，并让每条规则都能追溯到固定 commit 下的源码证据。

### 非目标

- 不为知识建库补写完整的 Mattermost 单元测试或端到端测试。
- 不默认运行 Mattermost 全量测试；已有测试只作为可选证据，疑难或高风险规则才选择性运行。
- 不逐行把全部源码发送给模型，也不把每个内部 helper 都提升成产品规则。
- 不要求一次运行完成全仓库；系统必须支持分域、分片、暂停和恢复。
- 本计划不扩展增量更新、Webhook 或企业权限体系；先解决成熟产品的首次存量建库。
- 不把代码实现声称为官方产品设计；产物定义为“固定 commit 下实际实现的行为知识”。

## 业务不变量与当前系统理解

本地 Mattermost 基线包含约 89.3 万行 Go、94.8 万行 TypeScript/JavaScript、184.4 万行常见源代码，具有 465 个 API4 路由注册、1749 个 App 方法、829 个 Go 测试文件和约 2100 个前端测试/spec 文件。当前 Channel Membership scope 只覆盖 4 个文件中的 13 个符号，不能代表成熟产品的存量建库方式。

本计划遵守以下不变量：

1. SourceBinding 只能由解析器根据真实 repo、commit、文件、符号和行范围绑定，模型不得生成来源身份。
2. 权限、条件运算符、允许/拒绝方向、actor、类型集合和状态变化必须保存为结构化字段，不能依赖自然语言摘要保持语义。
3. L2、L3、L4 是同一结构化规则的角色视图，不再采用 L1→L2→L3→L4 连续文本摘要作为事实传递机制。
4. 单个切片失败只能阻止或重试该切片，不得触发整个模块或仓库重新生成。
5. 开源样板不要求人工产品审核；只有通过技术门禁的高置信度规则可以自动发布，冲突、缺证据和低置信度规则进入隔离区。
6. 运行完成、JSON 合法或依赖 ID 存在不代表语义正确，不能作为发布条件。

## 目标架构

```text
Repository Snapshot
        ↓
Deterministic Repository Graph
        ↓
Entry Point Discovery
        ↓
Business Slice Planner
        ↓
Evidence + BehaviorRule IR
        ↓
Static Validation / Conflict Detection
        ↓
L2 Engineering View / L3 Product View / L4 User View
        ↓
Canonical Knowledge / Qdrant / QA
```

### Repository Graph

在固定 commit 上建立可复现的代码图，至少包含：

- 文件、语言、包、符号和内容 hash；
- HTTP/API、命令、定时任务、事件、WebSocket 和插件入口；
- 静态可解析的调用边；
- 权限常量、错误返回、状态/类型常量、配置和 Feature Flag 引用；
- Store 写入/删除、事件发布、插件调用和外部服务调用；
- 测试与生产符号的名称或调用关联。

首版优先支持 Mattermost Go 后端；前端索引用于补充 UI 入口、可见性条件和用户文案，不覆盖后端事实。

### Business Slice

以一个外部入口或一个内聚后台行为作为最小调度单位。每个切片保存入口、调用闭包、证据、输入 hash、状态、模型调用、验证结果、成本和耗时。

切片边界默认沿调用图扩展到以下停止点：

- Store/事务操作；
- 权限和策略服务；
- 消息、事件、插件和外部服务；
- 通用基础设施或超出当前领域的入口。

超过上下文预算时按决策簇继续拆分，不截断并伪装成完整结果。

### BehaviorRule IR

新增独立于展示文本的结构化事实源，最小字段包括：

```yaml
id: channel.member.remove.default_channel
domain: channel
capability: membership
actor: current_user
action: remove_member
resource: channel
conditions:
  all:
    - field: channel.name
      operator: equals
      value: default_channel
    - field: target.is_guest
      operator: equals
      value: false
decision: reject
state_changes: []
side_effects: []
exceptions: []
evidence: []
test_evidence: []
confidence: verified
```

条件树和枚举集合由程序校验。模型可以为字段归一化、规则合并和角色视图生成候选文本，但不能静默改变结构化谓词。

### 证据优先级

1. 当前 commit 的可执行生产代码；
2. 当前 commit 的已有单元/集成/端到端测试；
3. 当前 commit 对应的 API 契约和配置；
4. 产品与管理员文档；
5. 前端展示和提示文案。

已有测试默认只建立关联，不要求运行。只有源码含义不明确、证据冲突、权限/删除等高风险行为，才选择性读取或运行最相关测试。测试和源码冲突时保留冲突，不自动选择方便的一方。

## 修改范围

### 预计修改

- `app/code_index/`：仓库图、入口发现、调用边和证据探测器。
- `app/knowledge/`：BehaviorRule IR、规则合并、冲突检测、视图投影和覆盖率。
- `app/workflows/`：存量 bootstrap、切片状态机、检查点和恢复。
- `app/db/`：仓库快照、符号、切片、规则和运行记录的持久化模型。
- `scripts/`：仓库建图、试点运行、恢复、覆盖率报告和发布入口。
- `config/`：领域边界、入口模式、停止点和技术发布门禁。
- `tests/`：解析器、切片、IR、门禁、恢复和视图投影测试。
- `docs/architecture.md`、`docs/roadmap.md`：在里程碑通过后同步真实架构与状态。

### 明确排除

- QA 检索界面的重新设计。
- 全量 Mattermost 测试基础设施建设。
- 分布式队列、Kafka 或多机调度；先用本地持久化任务队列验证切片模型。
- 未经试点测量就承诺全仓完成时间或模型费用。

## 验收标准

### 功能验收

1. 给定 Mattermost commit，仓库图可重复生成；相同输入得到相同 symbol/entrypoint ID 和内容 hash。
2. API4 路由发现结果有明确的发现数、已分类数、无法解析数，任何遗漏或解析失败均显式报告。
3. 一个业务切片可以从入口追溯到涉及的权限、拒绝分支、状态变化、Store 操作和外部副作用，不要求包含无关 helper。
4. BehaviorRule 能无损表示 self/other、guest/non-guest、allow/deny、集合补集、布尔谓词和条件组合。
5. L2/L3/L4 从同一 BehaviorRule 生成；修改展示文案不能改变底层条件和 decision。
6. 切片产物按输入 hash 缓存；失败后恢复只执行未完成或失效切片。
7. 规则冲突、来源缺失、条件不完整或低置信度时禁止自动发布，并产生可检索的隔离原因。
8. 高置信度 Mattermost 规则无需人工产品审核即可写入 canonical knowledge，并能通过 QA 返回来源链路。

### 已知反例验收

Channel Membership 试点必须确定性通过以下反例，不能只依赖模型自评：

- 私有频道添加的 `PermissionManagePrivateChannelMembers` 检查适用于源码实际覆盖的全部目标，不得缩窄为“仅添加他人”。
- `removeChannelMember` 的允许类型集合为 `{Open, Private}`，不得只列举 Direct/Group 两个拒绝示例。
- 默认频道规则表达为“非访客移除被拒绝”，不得反转成“访客不能移除”。
- `FilterNonGroupChannelMembers` 返回空集合时，不能把 group member/non-group member 极性解释反。
- `IsDiscoverableSelfAddBlocked == true` 必须投影为阻止直接添加，而不是允许添加。

### 规模与效率验收

- Repository Graph 和入口发现阶段不调用 LLM。
- 任一模型请求只处理一个切片或一个有界决策簇，不发送整个模块的全部事实。
- 单切片失败不导致已完成切片重新调用模型。
- 所有运行记录模型、token、耗时、重试和结果状态。
- 全仓扩展前先运行不少于 20 个代表性 Channel 切片，给出实测吞吐、失败率、平均成本和全仓时间估算；没有该报告不得开始全仓模型编译。

### 覆盖率验收

覆盖报告至少提供：

- 入口：发现、分类、已编译、隔离、未处理；
- 决策：权限检查、拒绝分支、状态转换、持久化操作和外部副作用的覆盖数；
- 知识：BehaviorRule 与 Published L2/L3/L4 数量；
- 证据：有源码绑定、有已有测试关联、存在冲突的规则数；
- 领域：Channel、Team、User、Post 等领域的独立进度。

不以代码行数、模型调用成功数或生成文本数量代替业务覆盖率。

## 里程碑

### M1 — pending — Mattermost Go Repository Graph

- 为 Go 文件、符号、API4 路由和静态调用边定义稳定 ID。
- 在固定 commit 上生成仓库图和入口清单。
- 输出可复现性、解析失败和耗时报告。

验收：连续两次运行的入口和符号清单一致；解析失败显式列出；全阶段零 LLM 调用。

### M2 — pending — Channel Business Slice Planner

- 从 API4 Channel 入口生成 handler → App → Store/事件/插件的有界切片。
- 支持调用图停止点、超预算拆分和人工配置边界覆盖。
- 切片使用输入 hash 持久化并可恢复。

验收：Channel Membership 不再依赖手工枚举 13 个 symbol；任一切片失败后只重跑该切片。

### M3 — pending — BehaviorRule IR 与确定性探测器

- 实现条件树、actor/action/resource、decision、state change、side effect 和 evidence schema。
- 实现权限、类型集合、错误分支、Feature Flag、Store 和事件探测器。
- 模型只补充归一化与难以静态解释的语义。

验收：五个 Channel Membership 已知反例全部通过结构化断言。

### M4 — pending — 规则合并、冲突和角色视图

- 合并同一行为的多入口证据，保留全部 SourceBinding。
- 检测相反 decision、条件集合不一致和 actor 范围冲突。
- 从 BehaviorRule 独立生成 L2/L3/L4 视图。

验收：删除或修改任何 L3/L4 文案不会改变 BehaviorRule；冲突规则不能进入发布集。

### M5 — pending — Channel 代表性切片试点

- 选择不少于 20 个覆盖权限、CRUD、归档、成员、插件和事件的 Channel 切片。
- 使用 DeepSeek Flash 运行模型辅助步骤。
- 记录吞吐、成本、失败率、隔离率和规则准确性。

验收：形成是否具备全仓扩展条件的量化报告；未达到门槛时只修切片系统，不扩大扫描范围。

### M6 — pending — Channel 域存量基线

- 完成 Channel 领域入口分类和切片编译。
- 发布通过技术门禁的规则，隔离其余规则。
- 生成领域覆盖率并用代表性真实问题验证 QA 来源链路。

验收：Channel 覆盖报告无未解释的入口缺口；已发布问答均能回溯 BehaviorRule 和代码证据。

### M7 — pending — Mattermost 分域扩展

- 按 Channel 试点测得的吞吐和容量，依次扩展 Team、User、Post、Permission、Plugin 等领域。
- 每个领域独立记录范围、覆盖、隔离和完成状态。

验收：全仓入口均处于已发布、已隔离、明确非业务或待处理状态之一，不存在静默遗漏。

## 决策记录

### 2026-09-06 — 首次建库优先于增量更新

用户明确当前目标是从成熟产品的大量存量代码建立知识基线；新增代码少、变化小，因此增量维护不作为当前主线。

### 2026-09-06 — 测试是可选证据，不是建库前置工程

系统利用已有测试辅助消歧，但不要求为规则抽取新增或全量运行端到端测试。明确源码事实可以直接进入技术门禁；只有疑难、冲突或高风险规则才选择性使用测试。

### 2026-09-06 — 结构化规则取代连续文本摘要

Channel Membership 试验表明，整批 L1→L2→L3→L4 文本转换会产生条件反转、权限范围缩放和规则漏传。后续以 BehaviorRule 为唯一语义事实源，各层只生成面向角色的视图。

## 验证证据

- 方式：本地固定 Mattermost commit 的 Git 文件统计与源码模式统计。
- 结果：2363 个 Go 文件、5693 个前端源文件、465 个 API4 路由注册、1749 个 App 方法、829 个 Go 测试文件、约 2100 个前端测试/spec 文件。
- 能证明：当前样本达到成熟大型产品规模；人工 scope + 整批模型编译不适合作为全量建库方式。
- 未覆盖：尚未实现 Repository Graph，因此路由和方法统计是文本模式基线，不代表最终去重后的业务入口数。

## 下一验收项

完成 M1：定义稳定的 Repository Graph 数据模型，并在固定 Mattermost commit 上以零 LLM 调用生成首份 API4 路由与 Go symbol 清单、解析失败列表和可复现性报告。
