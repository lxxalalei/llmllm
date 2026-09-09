# Knowledge Assets

这里保存长期知识资产，而不是运行时 Agent Memory。

目录：

- `l1-engineering-facts/`：代码中观察到的工程事实
- `behavior-rules/`：从一个或多个 L1 形成的结构化业务语义，保存 actor、condition、decision、state change、side effect、exception 和 evidence
- `l2-engineering-rules/`：面向开发/测试的工程视图
- `l3-product-logic/`：面向产品/测试/支持人员的产品行为视图
- `l4-user-knowledge/`：按真实用户意图组织的 FAQ、操作说明、错误解释等知识

核心关系不是固定一一对应：

```text
L1 Engineering Facts (N)
        ↓
BehaviorRule (1..N)
        ├─ L2 Engineering View
        └─ L3 Product View

BehaviorRule (N) ↔ L4 User Intent (N)
```

一个业务规则可以由多个 L1 共同支撑；一个 L1 也可以拆出多个原子 BehaviorRule。L4 不由编译器强制为每条 Rule 生成一份，而是根据用户实际会问的问题建立，因此一条 Rule 可以没有 L4、可以对应多个 L4，一个 L4 也可以同时引用多个 Rule。

L2/L3 的关键业务语义必须能从 BehaviorRule 重建，不能依赖视图自行补回 Rule 中缺失的条件或权限。L4 可以组合多个已确认 Rule，但不能反过来为了预设 FAQ 去拼凑源码事实。

`KnowledgeItem.behavior_rule_id` 保留用于 L2/L3 和现有单 Rule 资产；L4 可以使用 `behavior_rule_ids` 关联多个规则。

L4 的同义问法放在 `question_variants`，与正文共同参与检索而不产生额外知识 ID。按用户意图编写和审核的标准由 [运行时规范](../app/llm/prompts/l4_authoring.md) 定义；生成与验收命令见 [使用说明](../docs/l4-user-intents.md)。未发布候选保存为知识目录之外的 JSON preview，不通过新增 Markdown 混入 canonical catalog。

KnowledgeItem 使用 Markdown + YAML Frontmatter；BehaviorRule 使用 YAML。稳定 ID 一旦发布不随文件名变化。发布状态、审核日期等维护信息放在 metadata 或 review/baseline 文档，不写进可检索知识正文。

SourceBinding 的核心职责是回到真实源码核对。成熟产品首次建库的核心证据使用 `repo + file + symbol`；commit/revision/line 可作为辅助定位信息，但不是知识身份或首次建库门禁。
