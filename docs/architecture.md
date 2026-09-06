# Architecture

## 1. 系统边界

本项目分为两个运行面，当前主线优先解决成熟产品的首次存量知识建库。

### Knowledge Build Plane

负责从已经成熟的大型产品源码中持续生产可检索、可追溯的长期知识资产。

```text
Mature Product Code
        ↓
Code Inventory / Business Scope
        ↓
L1 Engineering Facts
        ↓
BehaviorRule（结构化业务事实）
        ↓
L2 Engineering View
L3 Product View
L4 User View
        ↓
Publish / Index
```

L1 负责记录代码实际行为；BehaviorRule 用于保存不应在文本改写中丢失的条件、决策、状态变化和副作用；L2/L3/L4 是面向不同角色的知识视图，不再把连续文本摘要本身当成唯一事实传递机制。

### Knowledge Serve Plane

负责低延迟问答。

```text
User
 ↓
Identity / Role
 ↓
Layer Policy
 ↓
Retrieval
 ↓
Evidence
 ↓
Answer
```

普通用户优先 `L4 → L3`；产品/测试优先 `L3 → L2`；开发优先 `L2 → L1 → Code`。

## 2. 核心领域对象

### KnowledgeItem

系统中所有长期知识的统一抽象。关键字段包括 `id`、`layer`、`module`、`feature`、`content`、`status`、`derived_from`、`sources`、`visible_roles`。

### BehaviorRule

目标语义层。用于保存一个业务行为中真正需要稳定传递的结构，例如 actor、action、conditions、decision、state changes、side effects 和 evidence。

不是所有源码细节都必须进入 BehaviorRule；只有会影响产品行为、权限、状态或用户可见结果的事实才进入。

### SourceBinding

SourceBinding 的职责是“能回到真实源码核对”，不是构建代码变更追踪系统。

核心证据只要求：

```text
repo + file + symbol
```

`commit/revision`、`start_line/end_line` 可以在代码源能够稳定提供时作为辅助定位信息保存，但：

- 不作为知识身份；
- 不作为首次建库的前置条件；
- 不因为行号漂移触发知识重建；
- 不要求企业内部代码仓库具有 GitHub 式标准提交历史。

程序只需要保证文件和 symbol 真实存在，并把真实源码交给模型，避免模型伪造来源。

### KnowledgeRelation

保存 `derived_from / depends_on / related_to / affects / belongs_to`。

## 3. 存储职责

- Git / Markdown：正式知识资产和人工可审阅版本历史。
- PostgreSQL：运行数据、关系、状态、查询日志和后续需要的构建进度。
- Qdrant：搜索索引，不是知识真相源。

## 4. 工作流原则

### 成熟产品首次建库优先

当前系统服务的主要对象是已经运行多年、功能成熟、代码变化相对较少的产品。主线资源优先投入：

1. 找出业务模块和真实业务入口；
2. 确定一个 Feature 涉及的源码范围；
3. 从源码抽取 L1；
4. 保留关键条件、权限、状态变化和副作用；
5. 形成 L2/L3/L4；
6. 通过真实 QA 发现知识缺口并继续补库。

增量更新、Webhook、commit 对齐和行号推进属于已有维护能力，不得反过来主导知识构建架构。

### 可追溯即可，不做过度防御

源码验证的目标是防止幻觉和方便人工核对，不追求对每一次代码提交做强一致性证明。

除非真实业务问题证明有必要，否则不新增 SHA 链、复杂版本身份、全局行号同步或多层防伪校验。

### 业务语义优先于结构合法

JSON 合法、ID 唯一、`derived_from` 存在只能证明结构正确，不能证明业务语义正确。发布前真正需要关注的是：

- 条件是否反转；
- allow / deny 是否正确；
- actor 范围是否被扩大或缩小；
- 状态变化和副作用是否遗漏；
- L2/L3/L4 是否仍然表达源码支持的同一事实。

### 框架只负责执行

LangGraph 只负责 orchestration，不定义业务知识模型。即使未来替换 LangGraph，KnowledgeItem、BehaviorRule 和知识资产仍应保留。

## 5. 各层展示边界

```text
L1  开发/测试：代码实际上做了什么
L2  开发/测试：系统稳定的工程规则是什么
L3  产品/测试/客服：产品行为规则是什么
L4  普通用户：实际问题应该如何解释和处理
```

代码描述当前实现，不天然代表官方产品设计；自有产品的 L3 仍可保留产品审核边界。

## 6. 当前主线

- 扩大成熟产品已有源码的业务知识覆盖。
- 从手工枚举 symbol 逐步提升到按业务入口发现相关源码。
- 用 Channel Membership 继续验证 L1 与结构化业务规则的语义质量。
- 扩展 Channel Permission / Update / Archive & Restore。
- 建立按业务 Feature/领域统计的 Knowledge Coverage。
- 将 QA `knowledge_gap` 作为下一批知识构建优先级。

## 7. 次要维护能力

以下能力已经存在，但当前不作为主线阻塞项：

- Git Webhook / changed symbol detection；
- SourceBinding 反查受影响知识；
- L1/L2 增量重生成；
- L3 review / L4 outdated 传播；
- Qdrant 增量刷新。
