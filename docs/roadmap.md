# Roadmap

本文件是项目路线、状态和下一验收项的唯一索引。产品范围以 [PRD](PRD.md) 为准，架构边界以 [Architecture](architecture.md) 为准，实际实现状态以代码、配置、测试和运行结果为准。有界实施计划按 [开发计划约定](plans/README.md) 管理。

## 当前路线

- 当前主路线：`Phase 1 — 单模块纵向验证`
- 路线状态：`in_progress`
- 当前里程碑：`M1 — 冻结真实业务模块输入`
- 当前样本：Mattermost `Channel Creation`（频道创建）
- 下一验收项：将 Mattermost 固定 ref 的频道创建源码接入 `llmllm`，验证 Go 代码读取/解析边界，并执行频道创建基线测试或记录其环境依赖；完成后进入 M2 的真实 `Code → L1` 生成。
- 当前阻塞：无。若 Mattermost 基线测试依赖数据库或其他服务，则作为 M1 的环境依赖记录，不扩大首个功能范围。

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

## Phase 1 — 单模块纵向验证 (`in_progress`)

### 已选真实样本

- 上游仓库：`mattermost/mattermost`
- 上游默认分支：`master`
- 固定 ref：`43b2ae87e06b06abe01f9382ec26899c54c31728`
- 首个功能边界：`Channel Creation`（公开/私有频道创建，不扩展到 Direct/Group Channel、频道归档、搜索或完整 Channel 生命周期）
- 主要业务入口：`server/channels/app/channel.go`
  - `CreateChannelWithUser`
  - `CreateChannel`
- API 入口：`server/channels/api4/channel.go`
- 主要测试证据：
  - `server/channels/api4/channel_test.go`
  - `server/channels/app/channel_test.go`
- 产品规则审核责任：`llmllm` 项目负责人；代码事实以固定 ref 的 Mattermost 源码与测试为准。
- 有界实施计划：[Mattermost Channel Creation 纵向验证](plans/mattermost-channel-creation.md)

目标产物：

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

- `M1`（`in_progress`）：冻结 Mattermost Channel Creation 输入范围，并完成固定 ref 的本地读取、Go 解析边界与基线测试/环境依赖验证。
- `M2`（`pending`）：从真实代码生成并审核 L1/L2/L3/L4 资产，数量范围遵循本 Phase 定义。
- `M3`（`pending`）：验证角色检索边界和 L4 → Code 反向追溯。
- `M4`（`pending`）：基于可控代码变更样本验证影响定位与过期传播；不修改 Mattermost 上游仓库。

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
