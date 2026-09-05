# Phase 2 检索与问答 — 首个可实测闭环

- 状态：in_progress
- 路线：[Phase 2 — 检索与问答](../roadmap.md#phase-2--检索与问答-in_progress)
- 所有者：llmllm 项目
- 依赖：真实 LLM 凭据（已完成首轮实测）；Qdrant/Embedding 依赖 Docker 或外部端点（当前环境不可用）

## 目标与非目标

目标：让普通用户/产品/测试/开发能对 `knowledge/` 资产提问，得到 grounded、带引用、不越权的答案。

非目标：不把 Qdrant/向量检索伪装成已完成；不在本闭环做多轮对话、RAG 记忆、管理端分析看板。

## 已实现（2026-09-05）

- `app/knowledge/retrieval.py`：检索契约 + 本地 n-gram 评分（FAQ Direct Match 占位实现；替换点为 Qdrant retriever，函数签名不变）。
- `app/knowledge/qa.py`：grounded 回答器（OpenAI Responses API + strict json_schema；回答只允许引用已检索资产；引用经代码硬化，剔除伪造 id）。
- `app/api/routes/qa.py`：`POST /api/v1/qa {question, role, top_k}`；LLM 未配置时 503；空命中不调用模型直接返回 gap。
- 角色边界沿用 M3：检索输入 = 该角色可见资产（user 仅 published L3/L4，product/test 至 L2/L3，developer 至 L1 + 代码绑定）。
- 测试 31 passed（双 Python 环境）：检索排序/可见性、503、引用硬化、gap 透传、422 校验。

## 真实模型实测（2026-09-05，DS/DeepSeek-V4-Flash via qianji Responses 端点）

1. user「为什么我不能继续创建频道？」→ 命中 published limit FAQ，正确回答。
2. product「创建团队频道对类型和团队有什么要求？」→ 引用 published L3 team_channel + L2 standard_flow + 2 L4。
3. developer「频道数量上限逻辑在代码里怎么实现的？定位文件和函数」→ 引用 L1 team_limit，定位 mattermost/mattermost 43b2ae87 channel.go CreateChannelWithUser。
4. user「Mattermost 支持多人音视频会议吗？」→ knowledge_gap=true，不编造。

## 里程碑

- M1 — completed — QA API 真实模型实测通过（上述 4 问）。
- M2 — completed（2026-09-05）— Embedding Provider（GLM/Embedding-3）+ Qdrant 混合检索落地：
  - `app/knowledge/vector_index.py`：`knowledge_assets` 集合（cosine），UUID 稳定 point id，payload 存层/状态/visible_roles，user 角色过滤在 Qdrant 服务端执行；
  - `retrieval.retrieve_hybrid`：Qdrant dense 召回 + 本地 n-gram sparse 召回经 RRF 融合；
  - `scripts/sync_qdrant.py`：全量同步 + 孤儿清理；实测 31 资产入库；
  - QA 端点 `backend` 字段：`hybrid`（异常自动回退 `local` 并如实上报）；
  - Docker（WSL2 引擎）已部署；compose `restart: unless-stopped`。
- M3 — pending — Reranker、Query Analytics、Knowledge Gap 持久化、BM25 替换 n-gram。

## 验证证据

- 命令：`python -m pytest` → 34 passed（Python 3.12 / 3.14；Qdrant 集成测试无 Qdrant 环境自动跳过）；`python scripts/sync_qdrant.py` → `synced items=31 upserted=31 deleted=0`；真实演示 `.scratch/tx-m2-fixes/demo-hybrid-output.txt`（hybrid vs local 检索对比 + QA `backend: hybrid` 实测）。
- 结果：混合检索 top 命中正确（user/product/developer 各场景）；QA 引用全部为实际检索资产。
- 未覆盖：BM25/Reranker/Analytics/gap 持久化未落地；检索质量指标集未建立；WSL2 Docker 引擎重启后需 `docker compose up -d`（已设 `restart: unless-stopped` 自动拉起容器）。

## 完成记录

M1 完成。剩余风险与下一验收项见 `docs/roadmap.md`（Phase 2）。
