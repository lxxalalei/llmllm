# Roadmap

本文件是项目路线、状态和下一验收项的唯一索引。产品范围以 [PRD](PRD.md) 为准，架构边界以 [Architecture](architecture.md) 为准，实际实现状态以代码、配置、测试和运行结果为准。有界实施计划按 [开发计划约定](plans/README.md) 管理。

## 当前路线

- 当前主路线：`Phase 1 — 单模块纵向验证`
- 路线状态：`in_progress`
- 当前里程碑：`M2 — Code → L4`
- 当前样本：Mattermost `Channel Creation`
- 下一验收项：把 `build_l1` 从占位节点升级为真实 `Code → L1` 生成器。输入固定 Mattermost symbol 源码，输出结构化 `KnowledgeItem`，并与当前 12 条人工基准 L1 对比；不得用继续手工增加知识文件冒充自动生成能力。
- 当前阻塞：真实 LLM Provider 尚未接入。确定性代码解析、知识资产加载和 lineage 已可运行。

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

当前产物：

- L1：12 个，`draft`，均绑定固定 Mattermost repo/commit/file/symbol。
- L2：4 个，`draft`。
- L3：3 个，`review`，尚未作为产品真相发布。
- L4：6 个，`draft`，尚未向普通用户发布。
- 已实现 `KnowledgeCatalog`，可递归追溯 `derived_from`。
- 已实现 Knowledge Lineage API，可从 FAQ 找到固定 Mattermost 代码来源。

### 里程碑

- `M1`（`completed`）：固定 Mattermost 输入范围；Go parser 已实现；Compiler Preview 可解析 Go 源码并识别目标 symbol；Mattermost 自身 `go test` 命令已记录但未在当前环境实际执行，不宣称通过。
- `M2`（`in_progress`）：真实 L1/L2/L3/L4 基准资产已形成，但当前仍以人工审读代码后落盘为主；下一步必须实现自动 `Code → L1`。
- `M3`（`pending`）：完整角色检索边界尚未实现；L4 → Code 追溯能力已提前完成。
- `M4`（`pending`）：基于可控代码变更样本验证影响定位与过期传播。

### 当前验证证据

- Go parser 与 Compiler Go source analysis 已进入 CI。
- Knowledge Asset Loader、lineage、Knowledge API 已进入 CI。
- 最新 PR CI 已通过。
- 一次真实失败曾暴露 Markdown 资产缺少结构化 `title`；当前规则明确为：frontmatter 可提供 `title`，否则必须从首个 Markdown H1 获取，无 H1 则报错。

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
