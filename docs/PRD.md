# 企业产品知识助手 PRD

## 1. 产品信息

- 产品名称：企业产品知识助手
- 产品形态：企业内部知识生产与问答平台
- 目标企业规模：约 3000 人
- 主要用户：普通员工、产品、测试、开发、客服/支持人员
- 当前阶段：V1 / 成熟产品存量知识建库验证

## 2. 背景

成熟企业产品往往已经运行多年，真实规则大量存在于源码中，但知识分散在：

- 源代码；
- 开发文档；
- PRD；
- 测试经验；
- FAQ；
- 用户口口相传的信息。

常见问题：

1. 产品已经成熟，但很多规则只有开发通过读代码才能确认；
2. 产品、测试、客服和普通用户需要的是不同深度的解释；
3. FAQ 与开发文档容易不完整或过期；
4. AI 问答有检索能力，但底层知识本身不够结构化、不可追溯；
5. 直接让模型临时读代码回答，成本高、稳定性差、容易丢条件或产生幻觉。

因此需要先把成熟产品已有代码编译成长期知识资产，再为不同角色提供问答。

## 3. 产品定位

本产品不是单纯的 FAQ Bot，也不是 Coding Agent。

定位为：

> 以成熟产品源码为主要事实来源，把真实实现抽取为工程事实和结构化业务规则，再生成面向开发、产品和普通用户的不同知识视图，形成可长期沉淀、可追溯、可检索的企业产品知识体系。

系统分为两部分：

```text
知识生产系统
+
知识消费系统
```

知识生产：

```text
Mature Product Code
        ↓
Business Domain / Feature Scope
        ↓
L1 Engineering Facts
        ↓
BehaviorRule
        ├─ L2 Engineering View
        ├─ L3 Product View
        └─ L4 User View
        ↓
Canonical Knowledge
```

知识消费：

```text
企业员工
 ↓
身份 / 角色
 ↓
分层检索
 ↓
Grounded Answer
```

## 4. V1 核心目标

V1 首先解决：

> 一个已经成熟、代码变化不大的大型产品，如何从现有源码快速建立第一版高质量知识库。

核心结果：

- 业务域和 Feature 有明确知识覆盖；
- 关键规则能回到真实源码核对；
- 权限、条件、状态变化和副作用在不同知识视图中保持一致；
- 普通用户可以用自然语言获得稳定答案；
- 产品/测试可以下钻到工程规则；
- 开发可以继续下钻到 L1 和源码；
- QA 答不上的问题可以形成 Knowledge Gap，反向推动补库。

## 5. 非目标

V1 不重点解决：

1. 高频 Git commit / branch / webhook 跟踪；
2. 全局行号同步和复杂 revision identity；
3. 完整代码调用图或全仓 Repository Graph；
4. 完整 Coding Agent；
5. 自动修改生产代码；
6. 全公司所有代码一次性接入；
7. 多 Agent 自由协作；
8. 仅为了防御错误而增加复杂 SHA、防伪、签名或多级校验链；
9. 模型生成成功后无审核直接成为正式产品知识。

Phase 3 已有的增量维护能力保留，但不是当前主线。

## 6. 用户与知识视图

| 用户 | 主要视图 | 典型问题 |
|---|---|---|
| 普通员工 | L4 → L3 | 为什么不能操作、怎么用、状态是什么意思 |
| 产品 / 测试 / 客服 | L3 → L2 | 产品规则、权限、边界、异常、状态变化 |
| 开发 | L2 → L1 → Code | 工程规则、实现位置、真实源码行为 |

不同角色不维护独立知识库，而是消费同一套语义事实的不同视图。

## 7. 知识模型

### 7.1 Source / SourceBinding

源码证据的职责是：

1. 防止模型伪造来源；
2. 后续人工核对时能找到真实实现。

核心定位只要求：

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

`commit/revision`、`start_line/end_line` 是可选辅助信息，不作为：

- 知识身份；
- 首次建库门禁；
- 全局同步依据；
- 企业仓库必须具备的标准能力。

### 7.2 L1 — Engineering Facts

回答：

> 代码实际上做了什么？

重点记录：

- 权限检查；
- allow / deny；
- actor / target；
- 前置条件；
- 状态写入与删除；
- 特殊 bypass；
- 错误/拒绝分支；
- system post；
- WebSocket / event；
- plugin hook；
- 其他用户可见或业务相关副作用。

L1 不负责解释产品意图。

### 7.3 BehaviorRule — 结构化业务事实

BehaviorRule 是核心语义载体。

典型结构：

```yaml
actor: current_user
action: add_self_to_channel
resource: channel
conditions:
  all:
    - channel.type == private
    - channel.discoverable == true
decision: reject_direct_add
state_changes: []
side_effects: []
exceptions: []
evidence:
  - eng.mattermost.channel.membership.some_fact
```

目标不是把所有源码都结构化，而是稳定保存最容易在自然语言改写中丢失的：

- 条件；
- 作用对象；
- allow / deny；
- 状态变化；
- 副作用；
- 例外。

### 7.4 L2 — Engineering View

面向开发和测试，回答：

> 系统真正稳定的工程规则是什么？

L2 应综合多个 L1/BehaviorRule 事实形成工程规则，不把普通 HTTP 参数解析、handler 委派等机械细节升格成规则。

### 7.5 L3 — Product View

面向产品、测试、客服，回答：

- 谁可以做什么；
- 在什么条件下允许/拒绝；
- 成功后产品层面发生什么；
- 有哪些例外；
- 权限和状态如何变化。

L3 不暴露 Store、函数名和内部 hook 等实现细节。

### 7.6 L4 — User View

面向普通员工，主要包括：

- FAQ；
- 权限解释；
- 错误原因；
- 操作说明；
- 状态解释；
- 常见场景；
- “为什么我不能……”；
- “什么情况下可以……”。

L4 不自己创造事实，只表达 BehaviorRule 已经支持的业务语义。

## 8. 语义关系

核心语义关系：

```text
Code
 ↓
L1 Facts
 ↓
BehaviorRule
 ├─ L2 Engineering View
 ├─ L3 Product View
 └─ L4 User View
```

系统仍可保留 `derived_from` 作为 lineage，但核心事实不依赖 L2→L3→L4 连续文本摘要传递。

支持关系：

```text
derived_from
depends_on
related_to
affects
belongs_to
```

## 9. 知识状态

V1 使用：

```text
Draft
Review
Published
Outdated
Deprecated
```

原则：

> 模型生成成功 ≠ 正式发布。

BehaviorRule pipeline 当前默认输出 Draft。

## 10. 首次建库流程

```text
成熟产品源码
 ↓
确定业务域
 ↓
拆 Feature Scope
 ↓
读取真实源码 symbol
 ↓
生成 L1
 ↓
生成 BehaviorRule
 ↓
投影 L2 / L3 / L4
 ↓
语义审核
 ↓
写入 Canonical Knowledge
 ↓
同步检索索引
 ↓
真实 QA 验证
 ↓
Knowledge Gap
 ↓
继续补知识
```

首次建库不要求先做完完整调用图，也不要求对每次 commit 建立强版本身份。

## 11. 业务域与覆盖率

知识覆盖率按业务能力统计，不按代码行数统计。

例如 Mattermost Channel：

```text
Channel
├─ Creation
├─ Membership
├─ Permission
├─ Update / Privacy
└─ Archive / Restore
```

每个 Feature 至少记录：

- source files；
- symbols；
- L1 数量；
- BehaviorRule 数量；
- L2 数量；
- L3 数量；
- L4 数量；
- 当前审核/发布状态；
- QA 是否已验证。

## 12. 语义质量要求

结构合法不能替代语义审核。

重点检查：

- self / other 是否搞反；
- allow / deny 是否反转；
- actor 范围是否扩大或缩小；
- any / all 是否被误改；
- 权限条件是否遗漏；
- 状态变化是否遗漏；
- 副作用是否凭空增加；
- ordering 是否真的有源码依据；
- L3/L4 是否增加上游不存在的新事实。

不要求每个事实都增加一套防御性测试；真实业务风险高、已经发生过错误或公共逻辑复用时再补针对性测试。

## 13. 问答系统

知识生产与问答必须解耦。

不推荐：

```text
用户问问题
↓
临时读大量代码
↓
临时总结
↓
回答
```

推荐：

```text
Code
↓
提前建立知识
↓
Published Knowledge
↓
角色过滤检索
↓
Grounded Answer
```

问答必须：

- 只引用实际检索到的知识资产；
- 尊重角色可见边界；
- 缺乏知识时返回 Knowledge Gap，而不是猜测；
- 允许开发/产品按权限继续向下追溯。

## 14. 存储职责

### Git + Markdown/YAML

正式知识资产与人工可审阅版本历史，是 canonical knowledge。

### PostgreSQL

保存运行数据、关系、状态、查询日志和必要的构建记录。

### Qdrant

作为检索索引，不是真相源。

## 15. 增量维护

成熟产品代码变化较少，因此增量维护是次要能力。

已有能力可以在后续需要时完成：

```text
代码变化
↓
changed symbol
↓
受影响 L1
↓
影响关系传播
↓
Review / Outdated
```

但不要求首次建库围绕 commit、行号或 Webhook 设计主架构。

## 16. Mattermost Channel 当前验证域

当前样板域：

```text
Mattermost Channel
├─ Creation
├─ Membership
├─ Permission
├─ Update / Privacy
└─ Archive / Restore
```

项目已经具备五个 Feature scope 和域级编译入口。

下一阶段真实验收重点：

1. 用真实 Mattermost checkout 跑完整 Channel 域；
2. 生成完整 L1 / BehaviorRule / L2 / L3 / L4 preview；
3. 审核语义质量；
4. 形成 Channel Knowledge Coverage；
5. 发布通过审核的知识；
6. 用真实问题测试 QA；
7. 用 Knowledge Gap 决定下一批知识扩展。

## 17. V1 验收标准

一个 Feature 可以进入正式知识库，至少满足：

1. 绑定的 repo/file/symbol 真实存在；
2. L1 没有明显 unsupported fact；
3. BehaviorRule 的 actor、conditions、decision、state changes、side effects 有上游证据；
4. allow/deny、self/other、all/any 等关键语义没有反转；
5. L2/L3/L4 不添加 BehaviorRule 不支持的新事实；
6. 角色可见边界正确；
7. 代表性真实问题能用该知识回答；
8. 需要时能回到源码核对。

不要求：

- 固定行号；
- 每条知识固定 commit；
- 全仓一次完成；
- 一次模型输出零错误；
- 为每条规则新增测试；
- 在首次建库前完成完整 Repository Graph。

## 18. 设计原则

1. Mature Product First；
2. Knowledge First；
3. Code Is Evidence, Not Product Truth；
4. One Rule, Multiple Views；
5. Traceable, Not Over-Defensive；
6. Build Once, Serve Many；
7. Role-based Retrieval；
8. Framework Replaceable。
