# Roadmap

本文件是项目路线、状态和下一验收项的唯一索引。产品范围以 [PRD](PRD.md) 为准，架构边界以 [Architecture](architecture.md) 为准，实际实现状态以代码、配置、测试和运行结果为准。有界实施计划按 [开发计划约定](plans/README.md) 管理。

## 当前路线

- 当前主路线：`Phase 1 — 单模块纵向验证`
- 路线状态：`blocked`
- 当前里程碑：`M1 — 冻结真实业务模块输入`
- 下一验收项：明确一个可在本地读取和验证的真实业务模块，记录其仓库与 ref、模块边界、入口文件、业务负责人/审核人，以及可执行的基线测试。未满足前不得用仓库内示例资产冒充真实纵向验证。
- 当前阻塞：尚未提供真实业务模块及其可访问代码；这不影响继续维护 Phase 0 骨架，但阻止 Phase 1 业务闭环验收。

路线状态只使用：

- `pending`：尚未开始且无阻塞。
- `in_progress`：当前正在推进；默认只能有一条主路线处于此状态。
- `blocked`：缺少继续验收所需的输入、权限或外部条件。
- `completed`：可观察验收标准全部满足且有实际证据。
- `superseded`：已被明确的新路线取代，并保留替代原因和链接。

完成里程碑时，应在对应 Phase 下记录验证命令/方式、结果、证明范围和未覆盖项，再更新当前里程碑与下一验收项。

## Phase 0 — Bootstrap (`completed`)

- [x] FastAPI
- [x] Pydantic Knowledge Schema
- [x] LangGraph Compiler Skeleton
- [x] Tree-sitter Python Parser
- [x] PostgreSQL Schema
- [x] Qdrant Client
- [x] Knowledge Asset Directory
- [x] Tests / CI

基线验证（2026-09-05）：

- 命令/方式：在仓库外的临时虚拟环境安装 `.[dev]` 后执行 `python -m pytest`。
- 结果：`3 passed`；存在 2 条来自依赖库的弃用警告。
- 能证明：健康接口、确定性编译骨架顺序和 Python 顶层符号解析测试通过。
- 未覆盖：Docker Compose、PostgreSQL、Qdrant、真实业务模块和端到端用户链路。

## Phase 1 — 单模块纵向验证 (`blocked`)

选择一个真实业务模块：

```text
真实代码
→ 10~30 个 L1 Fact
→ 3~10 个 L2 Rule
→ 3~10 个 L3 Product Logic
→ 10~30 个 L4 FAQ
```

验收：

- 能从 L4 追溯到 Code
- 产品审核可以修改/发布 L3
- 普通用户只能检索 L3/L4
- 一处代码变化可以定位受影响知识

里程碑：

- `M1`（`blocked`）：冻结真实业务模块输入。阻塞条件见“当前路线”。
- `M2`（`pending`）：从真实代码生成并审核 L1/L2/L3/L4 资产，数量范围遵循本 Phase 定义。
- `M3`（`pending`）：验证角色检索边界和 L4 → Code 反向追溯。
- `M4`（`pending`）：修改一处已绑定代码并验证影响定位与过期传播。

Phase 0 中的示例知识和编译流程只用于证明骨架边界，不计入本 Phase 的真实业务验收证据。

## Phase 2 — 检索与问答 (`pending`)

- Embedding Provider
- Sparse / BM25
- Qdrant Hybrid Search
- Metadata / Role Filter
- Reranker
- FAQ Direct Match
- L3 Fallback
- Query Analytics
- Knowledge Gap

## Phase 3 — 增量知识编译 (`pending`)

- Git Webhook
- Diff Analyzer
- Changed Symbol Detection
- Impact Propagation
- L1/L2 自动更新
- L3 Review Queue
- L4 自动再生成

## Phase 4 — 企业化 (`pending`)

- SSO / IAM
- Department / Project Permission
- Review Console
- Version / Diff UI
- Evidence Trace
- Monitoring / Cost / Latency
- 灰度与回滚
