# Mattermost 规模的成熟产品存量知识建库

- 状态：in_progress
- 路线：Phase 4 — 规模化知识构建
- 所有者：Codex（实现与技术验收）

## 1. 目标

以 Mattermost 这类已经成熟、功能稳定、代码变化相对较少的大型 IM 产品作为规模样本，验证如何从大量已有源码建立可长期使用的企业产品知识库。

当前主目标不是追踪每次代码变化，而是回答：

1. 怎么从成熟产品中发现业务模块和业务入口；
2. 怎么确定一个 Feature 真正相关的源码范围；
3. 怎么从源码稳定抽出 L1 Engineering Facts；
4. 怎么保留权限、条件、状态变化和外部副作用，避免逐层文本摘要丢语义；
5. 怎么生成适合开发、产品和普通用户使用的 L2/L3/L4；
6. 怎么用真实 QA 发现知识缺口并继续补库。

## 2. 明确非目标

当前阶段不投入主要资源做以下事情：

- 高频 Git commit / branch / webhook 跟踪；
- 全局行号同步；
- 复杂 revision identity、SHA 链或防伪链；
- 为建库补写大量测试；
- 默认运行 Mattermost 全量测试；
- Kafka、分布式任务集群或多机调度；
- 为了“可维护”先建设一套复杂的代码变化平台。

Phase 3 已经实现的增量维护能力保留，但不作为成熟产品首次建库的阻塞条件。

## 3. 主链路

```text
成熟产品源码
    ↓
Code Inventory
    ↓
业务入口 / Feature Scope
    ↓
相关源码
    ↓
L1 Engineering Facts
    ↓
BehaviorRule
    ↓
L2 Engineering View
L3 Product View
L4 User View
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

SourceBinding 的目标只有两个：

1. 防止模型伪造源码来源；
2. 以后人工核对时能够回到真实代码。

核心证据只要求：

```text
repo
file
symbol
```

例如：

```yaml
source:
  repo: mattermost/mattermost
  file: server/channels/app/channel.go
  symbol: addUserToChannel
```

程序负责确认：

- 文件真实存在；
- symbol 真实存在；
- 交给模型的源码确实来自这个 symbol。

`commit/revision` 和 `start_line/end_line` 仅作为辅助定位信息：有稳定来源时可以保存，没有也不影响知识生成和发布。

它们不用于：

- 知识身份；
- 首次建库门禁；
- 行号漂移后的全量重绑；
- 要求企业内部仓库必须具备标准 Git 历史。

## 5. 每一层应该保存什么

### L1 — Engineering Facts

回答“代码实际上做了什么”。

重点包括：

- 权限检查；
- allow / deny 条件；
- actor / target；
- 状态写入和删除；
- 特殊 bypass；
- system post、WebSocket、plugin hook 等外部副作用。

不做产品意图推断。

### BehaviorRule — 结构化业务事实

用于保存文本改写时最容易丢失的语义，例如：

```yaml
actor: operator
action: add_member
resource: channel
conditions:
  - target_user.is_team_member == true
decision: allow
state_changes:
  - create channel_member
side_effects:
  - websocket user_added
```

BehaviorRule 是语义载体，不要求把每个源码细节都结构化。只有会影响业务规则、权限、状态或用户结果的内容才进入。

### L2 — Engineering View

面向开发和测试，回答“系统真正稳定的工程规则是什么”。

例如：

- 成员加入是权限、team membership、group constraint、policy、guard 的多层门禁；
- 成员移除不仅删除 ChannelMember，还清理依赖状态并触发生命周期通知。

HTTP 参数格式、普通 handler 委派等细节通常停留在 L1。

### L3 — Product View

面向产品、测试、客服，回答：

- 谁在什么条件下可以做什么；
- 什么情况下会被拒绝；
- 操作成功后产品层面发生什么；
- 有哪些例外。

不暴露 Store、函数名、内部 hook 等实现细节。

### L4 — User View

面向普通用户，主要是：

- FAQ；
- 权限解释；
- 错误原因；
- 操作说明；
- “为什么我不能……”；
- “什么情况下可以……”。

L4 不自行补事实，只从已经确认的业务规则生成用户表达。

## 6. 当前 Channel Membership 试点结论

真实模型链路已经跑通：

```text
Mattermost source
→ L1
→ L2
```

收紧后的真实结果为 49 条 L1 / 10 条 L2，结构校验通过，但仍发现：

- L1 重复；
- L2 抽象不稳定；
- 条件范围表达不严谨；
- plugin hook 顺序出现 unsupported ordering。

因此当前问题已经不是“模型能不能调用”，而是：

> 怎么让源码中的业务条件在知识抽象过程中不被反转、扩大、缩小或遗漏。

这也是引入 BehaviorRule 的主要原因。

## 7. 后续实施顺序

### M1 — 业务入口发现

目标：不再长期依赖人工手列 10～20 个 symbol。

先支持 Mattermost Channel 后端，从 API/handler 等外部入口出发，找到相关 App 方法和关键副作用。

验收重点：

- 能列出 Channel 的主要业务入口；
- 能看到哪些入口已处理、哪些还没处理；
- 不要求建立全仓完美调用图。

### M2 — Business Scope

把一个外部入口整理成可送模型理解的业务源码范围。

范围只扩展到真正影响行为的代码：

- 权限和策略；
- 状态写入/删除；
- 错误和拒绝分支；
- system post / event / websocket / plugin；
- 必要的内部 helper。

不把整个调用树无边界展开。

### M3 — L1 + BehaviorRule

继续使用模型抽 L1，但增加针对业务语义的 Review/Repair。

优先解决 Channel Membership 已经暴露的问题：

- self / other；
- guest / non-guest；
- allow / deny；
- 完整类型集合；
- ordering；
- actor/requestor；
- 状态变化和副作用。

通过后形成 BehaviorRule。

### M4 — L2/L3/L4 Views

从同一个 BehaviorRule 分别生成：

```text
开发/测试 → L2
产品/测试 → L3
普通用户 → L4
```

不再依赖 L1→L2→L3→L4 连续自然语言转述来传递核心条件。

### M5 — Channel 域扩展

顺序：

1. Channel Membership
2. Channel Permission
3. Channel Update
4. Channel Archive / Restore
5. 复核 Channel Creation

完成后形成 Channel 领域的第一版成熟知识基线。

### M6 — Coverage + QA Gap

覆盖率按业务能力统计，而不是按代码行数统计。

至少回答：

```text
Channel Creation      已覆盖
Channel Membership    已覆盖
Channel Permission    部分覆盖
Channel Update        未覆盖
Channel Archive       未覆盖
```

再用真实问题测试 QA。答不上来的问题进入 Knowledge Gap，作为下一批建库优先级。

## 8. 验收标准

一个知识 Feature 可以进入正式知识库，至少满足：

1. 源码文件和 symbol 真实存在；
2. L1 没有明显 unsupported fact；
3. 权限、allow/deny、actor、条件范围没有反转或扩大；
4. 关键状态变化和外部副作用没有明显遗漏；
5. L2 是工程规则，不是 L1 的机械改写；
6. L3/L4 不添加上游不存在的新事实；
7. QA 能使用该知识回答代表性真实问题并回到源码证据。

不要求：

- 每条知识绑定固定行号；
- 每条知识必须固定 commit；
- 为每条规则新增测试；
- 一次模型输出零错误；
- 全仓一次性完成。

## 9. 决策记录

### 2026-09-06 — 成熟产品首次建库优先

当前产品形态是成熟大型 IM，代码变化不是主要矛盾。系统首先解决“已有代码如何变成高质量知识”，增量维护保持次要位置。

### 2026-09-06 — SourceBinding 只承担可追溯

核心源码身份使用 `repo + file + symbol`。revision/commit/line 是可选定位信息，不参与知识身份和首次建库门禁，不建设以版本追踪为中心的防御性验证体系。

### 2026-09-06 — 结构化规则承接跨角色语义

L1 保留工程事实；BehaviorRule 保存关键业务条件和结果；L2/L3/L4 作为不同角色视图生成，减少连续文本摘要造成的语义漂移。

## 10. 下一验收项

继续使用 Channel Membership 作为样本，先把现有 L1/L2 结果中暴露的条件反转、重复、ordering 和副作用遗漏问题收敛成最小 BehaviorRule 表达，再验证同一规则生成 L2/L3/L4 时是否保持语义一致。
