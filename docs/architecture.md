# Architecture

## 1. 系统边界

本项目分为两个运行面，当前主线优先解决成熟产品的首次存量知识建库。

### Knowledge Build Plane

负责从已经成熟的大型产品源码中持续生产可检索、可追溯的长期知识资产。

```text
Mature Product Code
        ↓
Business Domain / Feature Scope
        ↓
L1 Engineering Facts
        ↓
BehaviorRule（结构化业务事实）
        ├─ L2 Engineering View
        ├─ L3 Product View
        └─ L4 User View
        ↓
Canonical Knowledge / Index
```

L1 负责记录代码实际行为；BehaviorRule 用于保存不应在文本改写中丢失的条件、决策、状态变化、副作用和例外；L2/L3/L4 是面向不同角色的知识视图，不再把连续文本摘要本身当成核心事实传递机制。

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

系统中所有长期知识的统一抽象。关键字段包括 `id`、`layer`、`module`、`feature`、`content`、`status`、`derived_from`、`sources`、`visible_roles`、`behavior_rule_id`。

### BehaviorRule

当前语义核心。用于保存一个业务行为中真正需要稳定传递的结构，例如：

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

不是所有源码细节都必须进入 BehaviorRule；只有会影响产品行为、权限、状态或用户可见结果的事实才进入。

同一条 BehaviorRule 可以投影出 L2/L3/L4，不需要把核心语义依次经过多轮自然语言摘要。

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

### KnowledgeDomainManifest

描述一个业务域由哪些 Feature scope 组成，并提供域级编译与覆盖率统计入口。

当前 Mattermost Channel 域包含：

```text
Channel Creation
Channel Membership
Channel Permission
Channel Update / Privacy
Channel Archive / Restore
```

### KnowledgeRelation

保存 `derived_from / depends_on / related_to / affects / belongs_to`。

## 3. 存储职责

- Git / Markdown：正式知识资产和人工可审阅版本历史。
- PostgreSQL：运行数据、关系、状态、查询日志和后续需要的构建进度。
- Qdrant：搜索索引，不是知识真相源。

## 4. 工作流原则

### 成熟产品首次建库优先

当前系统服务的主要对象是已经运行多年、功能成熟、代码变化相对较少的产品。主线资源优先投入：

1. 按业务域和 Feature 确定源码范围；
2. 从源码抽取 L1；
3. 把会影响业务行为的条件、权限、状态变化和副作用结构化为 BehaviorRule；
4. 从同一 BehaviorRule 生成 L2/L3/L4；
5. 形成可审核的 draft knowledge；
6. 通过真实 QA 发现知识缺口并继续补库。

增量更新、Webhook、commit 对齐和行号推进属于已有维护能力，不得反过来主导知识构建架构。

### 可追溯即可，不做过度防御

源码验证的目标是防止幻觉和方便人工核对，不追求对每一次代码提交做强一致性证明。

除非真实业务问题证明有必要，否则不新增 SHA 链、复杂版本身份、全局行号同步或多层防伪校验。

### 业务语义优先于结构合法

JSON 合法、ID 唯一、`derived_from` 存在只能证明结构正确，不能证明业务语义正确。真正需要关注的是：

- 条件是否反转；
- allow / deny 是否正确；
- actor 范围是否被扩大或缩小；
- 状态变化和副作用是否遗漏；
- L2/L3/L4 是否仍然表达 BehaviorRule 中的同一事实；
- BehaviorRule 本身是否真的得到 L1/源码支持。

### 生成不等于发布

模型成功产出 L1、BehaviorRule 或角色视图，只代表“生成成功”。

当前 BehaviorRule pipeline 默认输出 `draft`，不能因为 Structured Output 合法就自动成为正式知识。

### 框架只负责执行

LangGraph 只负责 orchestration，不定义业务知识模型。即使未来替换 LangGraph，KnowledgeItem、BehaviorRule 和知识资产仍应保留。

## 5. 各层展示边界

```text
L1  开发/测试：代码实际上做了什么
BehaviorRule 系统内部：真实业务条件、决策、状态与副作用
L2  开发/测试：系统稳定的工程规则是什么
L3  产品/测试/客服：产品行为规则是什么
L4  普通用户：实际问题应该如何解释和处理
```

代码描述当前实现，不天然代表官方产品设计；自有产品的 L3 仍可保留产品审核边界。

## 6. 当前实现状态

BehaviorRule 核心已经实现并接入新的 scope compiler。

Mattermost Channel 已形成完整可执行业务域：

```text
Channel
├─ Creation
├─ Membership
├─ Permission
├─ Update / Privacy
└─ Archive / Restore
```

域级编译入口：

```bash
python scripts/compile_domain.py \
  /path/to/mattermost \
  config/knowledge_domains/mattermost-channel.json \
  --output-dir .scratch/channel-domain \
  --summary .scratch/channel-domain-summary.json
```

当前还需要完成的不是继续扩基础结构，而是：

1. 在真实 Mattermost checkout + 模型凭据环境跑完五个 Channel Feature；
2. 审核完整 L1 / BehaviorRule / L2/L3/L4 的语义质量；
3. 形成第一版 Channel Knowledge Coverage；
4. 将通过审核的知识发布到 canonical Markdown / Qdrant；
5. 用代表性真实问题测试 QA，并把 gap 反馈到下一批知识构建。

自动 Repository Graph / 全仓调用图不再是进入这一步的前置条件；如果后续手工 scope 成本成为真实瓶颈，再按业务需要增加入口发现自动化。

## 7. 次要维护能力

以下能力已经存在，但当前不作为主线阻塞项：

- Git Webhook / changed symbol detection；
- SourceBinding 反查受影响知识；
- L1/L2 增量重生成；
- L3 review / L4 outdated 传播；
- Qdrant 增量刷新。
