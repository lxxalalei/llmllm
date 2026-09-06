# Roadmap

本文件是项目路线、状态和下一验收项的唯一索引。产品范围以 [PRD](PRD.md) 为准，架构边界以 [Architecture](architecture.md) 为准，实际实现状态以代码、配置、测试和运行结果为准。有界实施计划按 [开发计划约定](plans/README.md) 管理。

## 当前路线

- 当前主路线：`Phase 4 — 规模化知识构建 / Knowledge Expansion`
- 路线状态：`in_progress`
- 当前里程碑：`M1 — Mattermost Go Repository Graph`
- 当前样本：Mattermost 固定基线 `b3946ef5e2b85a27d365af2592cf1262de6a665e`，以完整成熟产品的首次存量建库为目标。
- 当前实施计划：[Mattermost 规模的成熟产品存量知识建库](plans/mattermost-scale-knowledge-bootstrap.md)
- 下一验收项：以零 LLM 调用生成稳定的 Mattermost API4 路由与 Go symbol 清单、解析失败列表和可复现性报告，为后续 Channel 业务切片建立 Repository Graph 基线。
- 当前阻塞：无。Phase 3 的增量维护基础能力已经具备，真实上游 change delivery/整链运行保留为维护能力验收债务，不再阻塞知识库扩容主线。

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
- 角色消费边界（M3，2026-09-05）：`GET /api/v1/knowledge?role=...`、详情/lineage/drill 端点支持 `role` 门控（不可见统一 404，防枚举）；`app/knowledge/views.py` 显式编码角色策略；`tests/test_role_views.py` 覆盖 user/product/test/developer 边界与下钻。Phase 3 开始前补充了 lineage 内部节点和 SourceBinding 的二次角色过滤，避免 user 从合法 FAQ 穿透到隐藏 L1/L2/code evidence。
- 影响定位与过期传播（M4，2026-09-05）：`app/knowledge/impact.py`（changed-symbol 检测按内容 hash，行漂移记为 shifted 不传播；绑定 L1 定位；反向 derived_from 闭包；状态建议 L1/L2→outdated、L3 published→review、L4 published→outdated）；`scripts/analyze_code_impact.py` dry-run/--apply；`tests/test_impact.py`。端到端报告：`.scratch/m4/impact-report.json`。

## Phase 2 — 检索与问答 (`completed`)

实施记录：[Phase 2 检索与问答（已归档）](plans/archive/phase2-retrieval-qa.md)

- [x] Embedding Provider（GLM/Embedding-3 via OpenAI 兼容 `/embeddings`，`EMBEDDING_MODEL` 配置，2026-09-05）
- [x] Sparse / BM25（自实现 BM25：CJK bigram + ASCII 词 token，k1=1.5/b=0.75，替换 n-gram 参与 RRF 融合）
- [x] Qdrant Hybrid Search（dense 角色过滤检索 + 本地 sparse n-gram 经 RRF 融合；`scripts/sync_qdrant.py` 全量同步含孤儿清理；检索后端 `hybrid` 异常自动回退 `local`，响应 `backend` 字段如实上报，2026-09-05）
- [x] Metadata / Role Filter（M3 角色消费边界；检索基于角色可见资产）
- [x] Reranker（LLM cross-encoder 式：候选扩至 2×top_k → 0-10 打分 → 截回 top_k；响应 `reranked` 字段；异常自动跳过，2026-09-05）
- [x] FAQ Direct Match（本地 n-gram 评分，接口契约可替换）
- [x] L3 Fallback（检索按角色覆盖 L2/L3/L4；user 仅 published L3/L4）
- [x] Query Analytics（PostgreSQL `query_logs` + `GET /api/v1/analytics/queries`：列表/筛选与聚合——总量、gap 率、backend 分布、top 命中、最近 gap；连接池 NullPool 跨事件循环安全，2026-09-05）
- [x] Knowledge Gap（QA 返回 `knowledge_gap` 并随 `query_logs` 持久化；`/api/v1/analytics/queries` 的 `summary.recent_gaps` 可查，2026-09-05）

已实现 QA 闭环（2026-09-05）：`POST /api/v1/qa`——按角色检索可见资产 → LLM 组织 grounded 答案（仅允许引用实际检索资产，cites 由代码硬化）→ 34 项测试通过（含 Qdrant 集成测试，无 Qdrant 环境自动跳过）。

Phase 2 M2（2026-09-05）：`app/knowledge/embeddings.py`（OpenAI 兼容 Embedding Provider）、`app/knowledge/vector_index.py`（Qdrant 索引：UUID 稳定 point id、payload 含层/状态/可见角色、角色过滤在服务端执行、全量同步孤儿清理）、`retrieval.retrieve_hybrid`（dense+sparse RRF）、`scripts/sync_qdrant.py`。真实同步 31 个资产 → `knowledge_assets`；QA 实测 `backend: hybrid` 回答正确且引用真实。本机 Docker（WSL2 引擎）已部署，compose 服务 `restart: unless-stopped`。

## Phase 3 — 增量知识维护基础 (`completed`)

实施计划：[Phase 3 增量知识编译](plans/phase3-incremental-compile.md)

- [x] Git Webhook / change intake：`POST /api/v1/webhooks/github` 接受 push，读取 GitHub compare。
- [x] Diff Analyzer：按已有 L1 SourceBinding 的 `repository + ref + baseline commit + file` 读取 before/after 源码；漏投 Webhook 时可从知识基线补追。
- [x] Changed Symbol Detection：沿用 Phase 1 的 symbol content hash；行漂移 `shifted` 不传播；当前 Go parser 对 receiver 同名 method 无法安全区分时显式失败。
- [x] Impact Propagation：L1 定位收紧到 `repo + commit + file + symbol`，再沿 `derived_from` 反向闭包生成影响报告。
- [x] L1 增量重生成核心：只重生成已有绑定且 changed 的 symbol；old/new facts 形成 unchanged/changed/added/removed diff；未变化事实仅推进 SourceBinding。
- [x] L2 增量重生成核心：仅在 L1 语义变化时基于当前完整 L1 feature scope 重新综合 L2，并形成 old/new diff。
- [x] L3 Review routing：只有 L2 真正变化才列出依赖它的 L3 Review 候选，不自动发布产品真相。
- [x] Mattermost M2 dry-run 入口：`scripts/regenerate_mattermost_change.py` 输出 L1/L2 diff + L3 Review JSON，不写正式 Markdown/Qdrant。
- [x] M3 publish plan：`scripts/publish_regeneration.py` 默认 dry-run，只有 `--approve` 才写 canonical Markdown/Git。
- [x] M3 状态安全：L3 进入 review 时，派生的 Published L4 同步变为 outdated，避免用户继续检索旧 FAQ。
- [x] M3 Qdrant 增量刷新：仅对 publish plan 涉及的 Knowledge ID upsert/delete；全量 `sync_qdrant.py` 保留作修复工具。

M1 代码级验证：PR #3 已合并，CI success；真实外部 GitHub Webhook delivery 尚未单独宣称通过。

M2 代码级验证：PR #4 已合并；CI 覆盖 changed/removed/unchanged L1、stable ID/version、SourceBinding commit/line 推进、L2 条件重生成、L3 Review routing、未绑定 symbol 隔离、同名 Go method/缺失 symbol/重复 Knowledge ID 显式失败，以及 Mattermost dry-run 在目标文件未变化时不调用 LLM。

M3 代码级验证：PR #5 已合并；最终 head CI #98 success，覆盖 publish dry-run/approve、Git 文件增删、SourceBinding 推进、L3 review → L4 outdated，以及 Qdrant 按 Knowledge ID 增量 upsert/delete。

未完成的真实验收：尚未用一次真实 Mattermost `channel.go` 上游变化执行 GitHub delivery → regeneration → review/publish → Qdrant 的完整外部链路。该项保留为 Maintenance Infrastructure 的端到端验收债务，不再作为当前知识扩容主线的阻塞项。

## Phase 4 — 规模化知识构建 (`in_progress`)

实施计划：[Knowledge Expansion — 规模化知识构建](plans/knowledge-expansion.md)

- [x] Repository Inventory：Go/Python 文件、top-level symbol、行范围，可限定目录/文件。
- [x] Batch Scope：一个 Feature 可绑定多个 source 文件和多个 symbol。
- [x] Batch Code → L1：每个 source 保留真实 SourceBinding，跨文件汇总。
- [x] Batch L1 → L2：基于当前 Feature 的完整 L1 集合统一综合工程规则。
- [x] Preview 与现有 Publish 接口兼容，新 Feature 可直接进入 dry-run / approve / Markdown / Qdrant。
- [x] Mattermost `Channel Membership` 首个 scope 描述。
- [ ] 对真实 Mattermost checkout 运行 Channel Membership L1/L2 模型编译并审核结果。
- [ ] 扩展 Channel Permission / Update / Archive & Restore。
- [ ] 增加 Knowledge Coverage Report。
- [ ] 将 QA `knowledge_gap` 转换为知识构建优先级输入。

当前原则：先把已有代码里的业务事实和工程规则持续抽出来，形成足够完整的知识库；问答、检索和增量维护能力作为已有基础设施服务知识生产，而不是反过来成为主线。

## Phase 5 — 企业化 (`pending`)

- SSO / IAM
- Department / Project Permission
- Review Console
- Version / Diff UI
- Evidence Trace
- Monitoring / Cost / Latency
- 灰度与回滚
