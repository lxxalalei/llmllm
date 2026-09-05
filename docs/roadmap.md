# Roadmap

本文件是项目路线、状态和下一验收项的唯一索引。产品范围以 [PRD](PRD.md) 为准，架构边界以 [Architecture](architecture.md) 为准，实际实现状态以代码、配置、测试和运行结果为准。有界实施计划按 [开发计划约定](plans/README.md) 管理。

## 当前路线

- 当前主路线：`Phase 2 — 检索与问答`（Phase 1 已于 2026-09-05 完成）
- 路线状态：`in_progress`
- 当前里程碑：`Phase 2 首个闭环 — 角色化检索 + LLM grounded 问答 API`（2026-09-05 完成并真实模型实测）
- 当前样本：Mattermost `Channel Creation`
- 下一验收项：把检索层从本地 n-gram 占位替换为可扩展索引——优先落地 Embedding Provider + Qdrant 混合检索（当前环境无 Docker/Qdrant，需先恢复该依赖），并补齐 Sparse/BM25、Reranker、Query Analytics 与 Knowledge Gap 持久化。
- 当前阻塞：无（Phase 1 全里程碑完成，2026-09-05）。CI 不执行外部付费模型调用。

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

## Phase 1 — 单模块纵向验证 (`completed`)

### 固定样本

- 上游仓库：`mattermost/mattermost`
- 固定 commit：`43b2ae87e06b06abe01f9382ec26899c54c31728`
- 功能边界：`Channel Creation`
- 核心文件：`server/channels/app/channel.go`
- 核心 symbol：`CreateChannelWithUser`、`CreateChannel`
- API 入口：`server/channels/api4/channel.go`
- 主要测试证据：`server/channels/app/channel_test.go`、`server/channels/api4/channel_test.go`
- 实施计划：[Mattermost Channel Creation 纵向验证](plans/archive/mattermost-channel-creation.md)

目标产物：

```text
真实代码
→ 10~30 个 L1 Fact
→ 3~10 个 L2 Rule
→ 3~10 个 L3 Product Logic
→ 10~30 个 L4 FAQ
```

当前产物与能力：

- L1：12 个人工基准事实，`draft`，均绑定固定 Mattermost repo/commit/file/symbol；另有 2 轮真实模型运行预览 JSON（17 条 / 27 条，均 `draft`、绑定全部通过），尚未入库。
- L2：4 个，`draft`。
- L3：Mattermost 3 个中 `team_channel` 已 `published`（2026-09-05 产品审核批准），`managed_category`/`space_availability` 保持 `review`；另有 conversation 示例 1 个 `published`。
- L4：Mattermost 10 个（8 `published` + 2 `draft`）；另 conversation 示例 1 个 `published`。
- Go/Python parser 与真实 source analysis 已实现。
- OpenAI Structured Outputs `Code → L1` 生成器已实现。
- L1 生成器只允许模型输出事实内容和 source symbol 名称；repo/ref/commit/file/行号由程序绑定并校验。
- `scripts/generate_mattermost_l1.py` 会校验固定 commit、目标文件无本地改动和目标 symbol，再执行真实生成。
- `KnowledgeCatalog`、lineage 与 Knowledge API 已实现。

### 里程碑

- `M1`（`completed`）：固定 Mattermost 输入范围；Go parser 与 Compiler source analysis 已通过 CI；Mattermost 自身 `go test` 命令已记录但未在当前环境实际执行，不宣称通过。
- `M2`（`completed`，2026-09-05）：真实模型固定样本运行与基准对比完成（12/12 概念覆盖、无重复与错误归因、source binding 100% 通过）；产品审核批准发布 L3 `team_channel`，派生发布 4 条 L4，新增 4 条 FAQ，Mattermost L4 达 10 条（8 published + 2 draft）。
- `M3`（`completed`，2026-09-05）：角色消费边界 API 已实现并通过测试（18 passed）——普通用户仅可消费 Published L3/L4；产品/测试可从 L3 下钻 L2（并保留 L1 给 test）；开发可从 L2/L1 定位固定 ref 代码；L4 → Code lineage 已提前完成。检索层（Qdrant）角色过滤属 Phase 2。
- `M4`（`completed`，2026-09-05）：可控样本（固定 commit channel.go 中 CreateChannel 插入一行注释）→ 检测唯一 modified symbol `CreateChannel`（其余 100+ 为行漂移 shifted，不传播）→ 定位 5 条绑定 L1 → 反向 derived_from 闭包 21 个受影响资产（5 L1 + 3 L2 + 3 L3 + 10 L4）→ 17 条状态迁移（L1/L2→outdated、L3 published team_channel→review、L4 published→outdated；review/draft 资产保持）。apply 在目录副本上实测生效，正式资产未改动。

### 当前验证证据

- Go parser、Compiler source analysis、L1 source binding、Knowledge Asset Loader、lineage、Knowledge API 均已进入 CI。
- Compiler 在未配置 provider 时明确记录 `l1_skipped_no_provider`，不再把占位流程标成 `l1_generated`。
- L2/L3/L4 未实现自动生成时明确记录 `*_not_implemented`，不生成虚假 artifact。
- 一次真实 CI 失败暴露 Markdown 资产缺少结构化 `title`；当前规则为 frontmatter `title` 或 Markdown H1，二者都缺失时直接失败。
- 真实 `Code → L1` 运行（2026-09-05）：固定 Mattermost checkout `43b2ae8`，OpenAI 兼容 Responses 端点 + Structured Outputs；修复 harness 后官方脚本直接运行 exit 0。与 12 条人工基准做概念级对比：12/12 覆盖、无重复、无错误归因、repo/commit/file/symbol/行范围绑定 100% 通过。细节见 `docs/plans/archive/mattermost-channel-creation.md`。
- 工具链修复（2026-09-05）：tree-sitter 收紧至 `<0.26`（0.26.0 与 tree-sitter-go 0.25.0 ABI 不兼容，真实文件解析产生越界行号/字节偏移）；extractor 增加 `close()`，生成脚本运行后显式关闭客户端（修复 Python 3.14 下 asyncio 收尾访问违例）；脚本 `file` 绑定改用 `as_posix()`，与资产目录路径格式一致。
- 角色消费边界（M3，2026-09-05）：`GET /api/v1/knowledge?role=...`、详情/lineage/drill 端点支持 `role` 门控（不可见统一 404，防枚举）；`app/knowledge/views.py` 显式编码角色策略；`tests/test_role_views.py` 覆盖 user/product/test/developer 边界与下钻。
- 影响定位与过期传播（M4，2026-09-05）：`app/knowledge/impact.py`（changed-symbol 检测按内容 hash，行漂移记为 shifted 不传播；绑定 L1 定位；反向 derived_from 闭包；状态建议 L1/L2→outdated、L3 published→review、L4 published→outdated）；`scripts/analyze_code_impact.py` dry-run/--apply；`tests/test_impact.py`。端到端报告：`.scratch/m4/impact-report.json`。

## Phase 2 — 检索与问答 (`in_progress`)

- [ ] Embedding Provider（依赖外部 embedding 模型/端点，未落地）
- [ ] Sparse / BM25（未落地；当前为本地 n-gram 占位）
- [ ] Qdrant Hybrid Search（当前环境无 Docker，未落地）
- [x] Metadata / Role Filter（M3 角色消费边界；检索基于角色可见资产）
- [ ] Reranker（未落地）
- [x] FAQ Direct Match（本地 n-gram 评分，接口契约可替换）
- [x] L3 Fallback（检索按角色覆盖 L2/L3/L4；user 仅 published L3/L4）
- [ ] Query Analytics（未落地）
- [x] Knowledge Gap（`/api/v1/qa` 返回 `knowledge_gap`；持久化记录未落地）

已实现 QA 闭环（2026-09-05）：`POST /api/v1/qa`——按角色检索可见资产（本地 n-gram，`app/knowledge/retrieval.py`）→ LLM 组织 grounded 答案（`app/knowledge/qa.py`，仅允许引用实际检索资产，cites 由代码硬化）→ 31 项测试通过；真实模型实测 4 问（user/product/developer + 盲区 gap）全部符合预期。

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
