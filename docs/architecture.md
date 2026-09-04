# Architecture

## 1. 系统边界

本项目分为两个运行面。

### Knowledge Build Plane

负责把代码和现有知识持续编译成长期知识资产。

```text
Git / Code
   ↓
Code Index
   ↓
L1 Engineering Facts
   ↓
L2 Engineering Rules
   ↓
L3 Product Logic
   ↓
Review
   ↓
L4 User Knowledge
   ↓
Publish / Index
```

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

系统中所有长期知识的统一抽象。关键字段包括 `id`、`layer`、`module`、`feature`、`content`、`status`、`version`、`derived_from`、`sources`、`visible_roles`。

### SourceBinding

将知识绑定回 `repo / commit / file / symbol / line`。

### KnowledgeRelation

保存 `derived_from / depends_on / related_to / affects / belongs_to`。

## 3. 存储职责

- Git：Markdown/YAML 正式知识资产和版本历史。
- PostgreSQL：KnowledgeItem 元数据、Relation、SourceBinding、状态和版本。
- Qdrant：搜索索引，不是知识真相源。

后续检索目标：`Dense Embedding + Sparse/BM25 + Metadata Filter + Rerank`。

## 4. 工作流原则

LangGraph 只负责 orchestration，不定义业务知识模型。即使未来替换 LangGraph，知识资产和领域模型仍应保留。

## 5. 人工审核边界

```text
Code → L1    高度自动化
L1 → L2      高度自动化
L2 → L3      需业务审核
L3 → L4      高度自动化
```

代码描述当前实现，不天然代表产品设计。

## 6. V1 之后的关键能力

- Git diff → changed symbols
- SourceBinding 反查受影响 L1
- Relation 向上遍历受影响 L2/L3/L4
- outdated / review 状态传播
- LLM Provider Adapter
- L4 FAQ Hybrid Search
- 企业 SSO / IAM
- Knowledge Gap 反馈闭环
