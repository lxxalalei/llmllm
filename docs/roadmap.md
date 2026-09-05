# Roadmap

本文件是项目路线、状态和下一验收项的唯一索引。产品范围以 [PRD](PRD.md) 为准，架构边界以 [Architecture](architecture.md) 为准，实际实现状态以代码、配置、测试和运行结果为准。有界实施计划按 [开发计划约定](plans/README.md) 管理。

## 当前路线

- 当前主路线：`Phase 1 — 单模块纵向验证`
- 路线状态：`in_progress`
- 当前里程碑：`M2 — Code → L4`
- 当前样本：Mattermost `Channel Creation`
- 下一验收项：在固定 Mattermost checkout 上执行真实 OpenAI `Code → L1`，将生成结果与 12 条人工基准 L1 对比，并记录遗漏、重复、错误归因和 source binding 是否正确。
- 当前阻塞：缺少可用于实际运行的 `LLM_API_KEY` / `LLM_MODEL`。生成器和本地验证 harness 已实现，CI 不执行外部付费模型调用。

路线状态只使用：`pending`、`in_progress`、`blocked`、`completed`、`superseded`。

## Phase 0 — Bootstrap (`completed`)

- [x] FastAPI
- [x] Pydantic Knowledge Schema
- [x] LangGraph Compiler Skeleton
- [x] Tree-sitter Python Parser
- [x] PostgreSQL Schema
- [x] Qdrant Client
- [x] Knowledge Asset Directory
- [x] Tests / CI

基线验证（2026-09-05）：`python -m pytest` → 3 passed。该证据只覆盖 bootstrap 骨架。

## Phase 1 — 单模块纵向验证 (`in_progress`)

### 固定样本

- 上游仓库：`mattermost/mattermost`
- 固定 commit：`43b2ae87e06b06abe01f9382ec26899c54c31728`
- 功能边界：`Channel Creation`
- 核心文件：`server/channels/app/channel.go`
- 核心 symbol：`CreateChannelWithUser`、`CreateChannel`
- API 入口：`server/channels/api4/channel.go`
- 主要测试证据：`server/channels/app/channel_test.go`、`server/channels/api4/channel_test.go`
- 实施计划：[Mattermost Channel Creation 纵向验证](plans/mattermost-channel-creation.md)

目标产物：

```text
真实代码
→ 10~30 个 L1 Fact
→ 3~10 个 L2 Rule
→ 3~10 个 L3 Product Logic
→ 10~30 个 L4 FAQ
```

当前产物与能力：

- L1：12 个人工基准事实，`draft`，均绑定固定 Mattermost repo/commit/file/symbol。
- L2：4 个，`draft`。
- L3：3 个，`review`，尚未作为产品真相发布。
- L4：6 个，`draft`，尚未向普通用户发布。
- Go/Python parser 与真实 source analysis 已实现。
- OpenAI Structured Outputs `Code → L1` 生成器已实现。
- L1 生成器只允许模型输出事实内容和 source symbol 名称；repo/ref/commit/file/行号由程序绑定并校验。
- `scripts/generate_mattermost_l1.py` 会校验固定 commit、目标文件无本地改动和目标 symbol，再执行真实生成。
- `KnowledgeCatalog`、lineage 与 Knowledge API 已实现。

### 里程碑

- `M1`（`completed`）：固定 Mattermost 输入范围；Go parser 与 Compiler source analysis 已通过 CI；Mattermost 自身 `go test` 命令已记录但未在当前环境实际执行，不宣称通过。
- `M2`（`in_progress`）：人工 L1-L4 基准资产与真实 `Code → L1` 生成代码均已存在；尚缺一次带真实模型凭据的固定样本运行和基准对比，L4 数量仍为 6/10~30。
- `M3`（`pending`）：完整角色检索边界尚未实现；L4 → Code 追溯能力已提前完成。
- `M4`（`pending`）：基于可控代码变更样本验证影响定位与过期传播。

### 当前验证证据

- Go parser、Compiler source analysis、L1 source binding、Knowledge Asset Loader、lineage、Knowledge API 均已进入 CI。
- Compiler 在未配置 provider 时明确记录 `l1_skipped_no_provider`，不再把占位流程标成 `l1_generated`。
- L2/L3/L4 未实现自动生成时明确记录 `*_not_implemented`，不生成虚假 artifact。
- 一次真实 CI 失败暴露 Markdown 资产缺少结构化 `title`；当前规则为 frontmatter `title` 或 Markdown H1，二者都缺失时直接失败。

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
