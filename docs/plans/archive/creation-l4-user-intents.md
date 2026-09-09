# Creation L4 用户意图试点

- 状态：completed
- 路线：[Phase 4](../../roadmap.md)
- 所有者：主 Agent；内容、模型适配、离线评估由三个 worker 在独立 worktree 负责。
- 依赖：现有 Creation BehaviorRule、L3 及 L4 资产。

## 目标与非目标

建立可执行的 L4 写作规范、先规划后写作再审核的模型入口，以及五个完整用户问题的草稿样本与离线检索验收。原子 Rule 保留，L4 按用户意图组合 Rule，同义问法共享一个知识 ID。

不改写 canonical knowledge、不发布、不退役旧资产、不增加框架或依赖。模型真实问答和线上发布另行验收。本次不修复已有 review 权限问题；评估使用普通用户正常检索，在独立内存目录模拟发布。

## 修改范围与协作边界

- 主 Agent：领域类型和编译约束、CLI、question_variants 持久化和检索、业务测试、文档与整合验收。
- 内容 worker：Creation 意图配置、五条草稿 JSON、内容审阅报告、问题集及其测试。
- 模型 worker：L4 provider、运行时 Markdown 规范及 fake API 测试。
- 评估 worker：内存评估器、评估 CLI 及测试。

## 验收标准

1. 模型仅能引用给定的 Rule；层级、权限、草稿状态和 L3 血缘由代码决定。
2. 支持 create / merge / gap；缺证据时停止写作；合并不触及原始文件。
3. 同义问法能往返 Markdown 并参与 BM25 与 embedding 输入。
4. 五条样本回答完整问题，提供证据和缺口记录；至少十二道含同义与缺口的问题验证候选检索。
5. 报告区分检索命中、自动问答检查和语义人工验收，离线检索不能冒充真实 QA。

## 决策记录

- 运行时规范和领域校验共同约束生成；模型审核结果仅为候选意见，不授予发布权限。
- 现有 roadmap 的“新基线均恢复 review”与资产实际状态冲突：目前部分 Creation、Membership、Permission、Update 已 published。以文件状态为准；published 不代表已有真实 QA 证据。本次不追认或撤回这些状态。
- 运行时拒绝创建第四个新 worker，复用现有空闲 worker 完成第三项，三个子任务仍在独立 worktree 中执行。

## 验证证据

业务测试先覆盖缺失编译入口、CLI 输出隔离、未知 Rule、跨范围证据、重复合并、失败路径缺口等失败场景，再实现和修正。主 Agent 独立检查所有 worker 交付，仅整合专属文件；额外修正了成功路径反推失败行为、同 ID 合并的泄露误报、候选拒绝仍可能令 CLI 通过，以及空评审标准不能代表语义已通过。

2026-09-09 相关回归：

```bash
env -u ALL_PROXY -u all_proxy -u HTTPS_PROXY -u https_proxy -u HTTP_PROXY -u http_proxy \
  .venv/bin/python -m pytest -q \
  tests/test_l4_compiler.py tests/test_l4_provider.py tests/test_l4_evaluation.py \
  tests/test_l4_question_variants.py tests/test_creation_l4_candidates.py \
  tests/test_compile_l4_script.py tests/test_knowledge_assets.py \
  tests/test_behavior_rule_assets.py tests/test_behavior_scope_compiler.py \
  tests/test_publish.py tests/test_vector_index_incremental.py \
  tests/test_llm_reasoning.py tests/test_review_mode.py \
  tests/test_visibility_modes.py tests/test_qa_assistant.py
```

- 结果：81 passed。存在既有 Starlette 弃用警告，以及 Qdrant 客户端无法查询服务版本的警告。
- 原代理环境下，增量向量客户端测试曾因缺少 `socksio` 在构造时失败；仅对子进程移除代理变量后通过，没有新增依赖或改动用户代理配置。
- 能证明：编译边界、同义词 Markdown 往返与 embedding 输入、fake API 三阶段接入、内存候选替换、CLI 失败判定、既有资产和 Serve 状态行为未回归。
- 未覆盖：真实模型内容质量、真实数据库/向量服务、HTTP 端到端使用。fake API 与 fake responder 均不能当作真实模型验证。
- 最后对“没有 rubric 也仍需语义审阅”的报告修正，定向重跑 `tests/test_l4_evaluation.py`：8 passed；重跑离线 CLI 仍通过。

离线 CLI 命令、逐题排名例外及证明边界见 [Creation 审阅报告](../../baselines/creation-l4-review-2026-09-08.md)。实际结果：5 候选、15/15 top-4 命中、13/15 top-1、0 退役 ID 残留；真实 QA 执行数 0，5 道缺口题的拒答表现仍待验证。

`git diff --check` 与新增 Python 模块 `compileall` 通过。`knowledge/` 下仅 README 文档变化，canonical Markdown/YAML 资产无增删或状态变化。

## 完成记录

本轮目标为规范、独立生成入口、参考草稿和离线验收工具，均已交付。参考样本是人工与 Agent 整理，不是实际三阶段模型产物。未提交、推送或发布；保留现有长期知识资产。

## 下一轮规划检查点

当前无下一轮计划。后继候选为真实模型生成与 QA、补齐操作/运行时配置证据、扩展其他 Feature、正式迁移旧知识；这些方向的范围与优先级需要选择，未自动启动实现或发布。已有知识发布必须以真实 QA 和审阅证据为前置。
