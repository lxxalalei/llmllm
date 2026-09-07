# Knowledge Assets

这里保存长期知识资产，而不是运行时 Agent Memory。

目录：

- `l1-engineering-facts/`：代码中观察到的工程事实
- `behavior-rules/`：从 L1 形成的结构化业务语义，保存 actor、condition、decision、state change、side effect、exception 和 evidence
- `l2-engineering-rules/`：面向开发/测试的工程视图
- `l3-product-logic/`：面向产品/测试/支持人员的产品行为视图
- `l4-user-knowledge/`：FAQ、操作说明、错误解释等用户视图

L2/L3/L4 的关键业务语义应来自同一个 BehaviorRule，而不是依次依赖自然语言摘要传递事实。

KnowledgeItem 使用 Markdown + YAML Frontmatter；BehaviorRule 使用 YAML。稳定 ID 一旦发布不随文件名变化。

SourceBinding 的核心职责是回到真实源码核对。成熟产品首次建库的核心证据使用 `repo + file + symbol`；commit/revision/line 可作为辅助定位信息，但不是知识身份或首次建库门禁。
