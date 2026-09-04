# Roadmap

## Phase 0 — Bootstrap

- [x] FastAPI
- [x] Pydantic Knowledge Schema
- [x] LangGraph Compiler Skeleton
- [x] Tree-sitter Python Parser
- [x] PostgreSQL Schema
- [x] Qdrant Client
- [x] Knowledge Asset Directory
- [x] Tests / CI

## Phase 1 — 单模块纵向验证

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

## Phase 2 — 检索与问答

- Embedding Provider
- Sparse / BM25
- Qdrant Hybrid Search
- Metadata / Role Filter
- Reranker
- FAQ Direct Match
- L3 Fallback
- Query Analytics
- Knowledge Gap

## Phase 3 — 增量知识编译

- Git Webhook
- Diff Analyzer
- Changed Symbol Detection
- Impact Propagation
- L1/L2 自动更新
- L3 Review Queue
- L4 自动再生成

## Phase 4 — 企业化

- SSO / IAM
- Department / Project Permission
- Review Console
- Version / Diff UI
- Evidence Trace
- Monitoring / Cost / Latency
- 灰度与回滚
