# AGENTS.md

## 项目目标

构建企业产品知识编译与问答平台。长期知识资产是第一优先级，Agent/Workflow 框架只是可替换基础设施。

## 开发约束

1. 优先实现真实业务闭环，不为了“架构完整”增加无业务价值的抽象。
2. 不把 LangGraph State、Agent Memory、Qdrant Vector 当作长期知识资产。
3. 不新增 CrewAI/AutoGen 等多 Agent 框架，除非出现明确且无法由现有 workflow 解决的需求。
4. 不为未知风险预埋复杂校验、哈希链、冗余状态机或 fallback。
5. 错误应尽量暴露真实原因，不以静默 fallback 掩盖问题。
6. 修改业务行为时先更新/新增业务测试，再实现代码。
7. 测试应验证用户/业务行为，而不是只验证内部实现细节。
8. 小修改优先运行相关测试，不默认每次跑全量测试。
9. 框架代码与领域代码分离，领域模型不得依赖 LangGraph。
10. 知识层级和权限策略必须由代码显式控制，不依赖 Prompt 自觉。

## 当前技术基线

- Python / FastAPI
- Pydantic
- LangGraph
- Tree-sitter
- PostgreSQL
- Qdrant
- Git + Markdown/YAML

## 第一阶段禁止扩展

除非任务明确要求，否则不要主动加入 Kubernetes、Kafka、Neo4j、Redis、CrewAI、AutoGen、LlamaIndex、Haystack、复杂 Agent Memory 或多层 Repository/Service 抽象。新增依赖前先证明现有技术不能直接解决。
