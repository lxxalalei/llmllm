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
        └─ L3 Product View

BehaviorRule(s)
        ↕
L4 User Intent Knowledge
        ↓
Canonical Knowledge / Index
```

L1 负责记录代码实际行为；BehaviorRule 用于保存不应在文本改写中丢失的条件、决策、状态变化、副作用和例外；L2/L3 是同一结构化规则的角色视图。L4 不要求和 BehaviorRule 一一对应，而是按真实用户意图组织，可以引用一个或多个 Rule，也可以不存在。

典型关系是：

```text
多个 L1 → 一个 BehaviorRule
一个 L1 → 多个原子 BehaviorRule
一个 BehaviorRule → 0..N 个 L4
多个 BehaviorRule → 一个 L4
```

因此知识质量不以各层数量相等为目标。

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

正常 Serve 只消费 `published` 资产。Draft/Review/Outdated 仅在显式 Review 模式中用于知识审核，不能因为角色是产品、测试或开发就自动进入正常问答候选。

## 2. 核心领域对象

### KnowledgeItem

系统中所有长期知识的统一抽象。关键字段包括 `id`、`layer`、`module`、`feature`、`content`、`status`、`derived_from`、`sources`、`visible_roles`、`behavior_rule_id`、`behavior_rule_ids`。

`behavior_rule_id` 继续服务单 Rule 的 L2/L3 和兼容已有资产；`behavior_rule_ids` 用于 L4 等需要组合多个业务规则的用户意图知识。

### BehaviorRule

当前语义核心。用于保存一个足够原子的业务行为中真正需要稳定传递的结构，例如：

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

Rule 的粒度以“自身足以表达完整条件和结果”为准。若一个 Rule 只能写成“根据 actor/target/type 再决定具体权限”，而具体权限仍需要从 L1 或人工解释中补回来，就说明 Rule 过粗，应拆成更原子的规则。

L2/L3 必须能从 BehaviorRule 本身重建核心语义；不能由视图重新读取 L1 后补回 Rule 中遗漏的信息。

### L4 User Intent Knowledge

L4 是用户真实问题的知识资产，不是 BehaviorRule 的机械翻译层。

例如同一个成员添加 L1 可以拆成：

```text
公开频道 self-add 权限
公开频道 add-other 权限
私有频道 add-member 权限
Direct/Group 普通加人入口拒绝
```

其中前两条 Rule 可以共同支撑一个用户问题：

```text
“为什么我能自己加入公开频道，却不能把别人加入？”
```

其他 Rule 如果暂时没有真实用户意图，可以没有 L4。

当前独立入口 `scripts/compile_l4.py` 读取意图清单和 canonical Rule，执行 `plan → write → review`，输出 JSON 草稿预览。意图规划支持 `create / merge / gap`。领域代码验证 Rule/L1/L3 的范围、已审核证据、稳定 ID 和合并冲突；模型只选择给定 Rule 并撰写正文，不能决定 L4 层级、权限、血缘或发布状态。写作与审核共享运行时加载的 [规范](../app/llm/prompts/l4_authoring.md)。

`question_variants` 随 Markdown metadata 保存，与标题、正文共同参与本地 BM25 和向量 embedding 输入。它们共用一个知识 ID，引用仍指向该知识。已有向量索引只有在后续正常同步后才会使用新问法。

`scripts/evaluate_l4.py` 在内存中模拟候选替换，使用普通用户的正常检索策略；不写 canonical，不连接数据库。可选择真实 QA responder，但检索命中和自动引用检查均不等于答案语义验收。详见 [使用流程](l4-user-intents.md)。此入口独立于现有 LangGraph skeleton 和 scope compiler，未自动接入全域编译。

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
3. 把会影响业务行为的条件、权限、状态变化和副作用结构化为足够原子的 BehaviorRule；
4. 从 Rule 形成 L2/L3 角色视图；
5. 按真实用户意图建立 0..N 个 L4，并允许一个 L4 组合多个 Rule；
6. 形成可审核的知识资产；
7. 通过真实 QA 发现知识缺口并继续补库。

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
- Rule 是否完整保存了视图所依赖的核心条件；
- L2/L3 是否仍表达同一条 Rule；
- L4 组合的多个 Rule 是否共同支撑用户答案；
- BehaviorRule 本身是否真的得到 L1/源码支持。

### 生成不等于发布

模型成功产出 L1、BehaviorRule 或角色视图，只代表“生成成功”。

当前 BehaviorRule pipeline 默认输出 `draft`，不能因为 Structured Output 合法就自动成为正式知识。Semantic Review 通过后进入 `review`；真实 QA 验收后才进入 `published`。

### 维护信息不进入知识正文

发布日期、审核状态、待确认事项等属于 metadata 或 review/baseline 文档，不写入 L2/L3/L4 正文，避免污染 BM25、Embedding 和最终回答上下文。

### 框架只负责执行

LangGraph 只负责 orchestration，不定义业务知识模型。即使未来替换 LangGraph，KnowledgeItem、BehaviorRule 和知识资产仍应保留。

## 5. 各层展示边界

```text
L1  开发/测试：代码实际上做了什么
BehaviorRule 系统内部：真实业务条件、决策、状态与副作用
L2  开发/测试：系统稳定的工程规则是什么
L3  产品/测试/客服：产品行为规则是什么
L4  普通用户：围绕真实问题如何解释和处理
```

代码描述当前实现，不天然代表官方产品设计；自有产品的 L3/L4 仍可保留产品审核边界。

## 6. 当前实现状态

BehaviorRule 核心已经实现并接入新的 scope compiler。

Mattermost Channel 五个核心 Feature 已经形成第一版源码支撑的知识基线：

```text
Channel
├─ Creation
├─ Membership
├─ Permission
├─ Update / Privacy
└─ Archive / Restore
```

第一版基线已经完成源码语义核查和 Coverage 记录，但此前曾出现“尚未经过真实 QA 就批量 Published”的发布错误。历史上曾回退到 `review`；截至本轮核查，Creation、Membership、Permission、Update 中已有 Published 资产，不能再把“全部 review”当作当前事实。文件状态不代表已完成真实 QA，参见 [当前覆盖和缺口](baselines/channel-coverage-vs-gap-2026-09-08.md)。正常 Serve 只消费 Published 资产。

同时已经开始修正一一对应模型：BehaviorRule 自动投影只生成 L2/L3；L4 改为用户意图资产并支持多个 `behavior_rule_ids`。Membership 的 `add_permission_split` 已作为第一处样例从一条过粗 Rule 拆成四条原子 Rule，并用其中两条共同支撑一条 FAQ。

域级编译入口仍保留：

```bash
python scripts/compile_domain.py \
  /path/to/mattermost \
  config/knowledge_domains/mattermost-channel.json \
  --output-dir .scratch/channel-domain \
  --summary .scratch/channel-domain-summary.json
```

当前主任务不是继续扩基础结构，而是：

1. 审核剩余 Channel BehaviorRule 是否仍有过粗或语义缺失；
2. 清理旧 Creation 与新基线的重复/冲突知识，保留真正有独立用户意图价值的 L4；
3. 用代表性真实问题执行 QA 验收；
4. 逐 Feature 发布通过 QA 的资产，而不是整批状态翻转；
5. 再根据 Knowledge Gap 决定补哪些 Channel 子能力或进入下一个业务域。

自动 Repository Graph / 全仓调用图不再是进入这一步的前置条件；如果后续手工 scope 成本成为真实瓶颈，再按业务需要增加入口发现自动化。

## 7. 次要维护能力

以下能力已经存在，但当前不作为主线阻塞项：

- Git Webhook / changed symbol detection；
- SourceBinding 反查受影响知识；
- L1/L2 增量重生成；
- L3 review / L4 outdated 传播；
- Qdrant 增量刷新。
