# 临时放行决定：Channel 模块人工审核默认通过 — 2026-09-09

## 决定

用户指示：按当前流程直接运行代码，人工审核环节暂时默认放行。理由：当前只有 Mattermost Channel 一个业务域，Serve 侧缺少可用的有效知识，需要先把该模块资产推进到可服务状态，验证整条链路能产出真实可答的知识。

- 范围：仅 mattermost.channel 模块（Creation / Membership / Permission / Update-Privacy / Archive-Restore）。
- 生效方式：knowledge/ 下 frontmatter status 为 draft / review 的资产翻转 published；deprecated / outdated 不动；BehaviorRule YAML 无状态字段、不动。
- 临时性：适用于本轮运行；恢复人工审核后，新资产继续按 draft -> review -> published 治理。
- 机器检查仍保留：本次不跳过任何代码执行的校验、不手工编造正文、不修改资产内容，只做状态翻转。

## 风险记录（不静默）

- 本决定与 docs/roadmap.md “QA 前不得批量发布、逐 Feature 发布”决策冲突，且历史上发生过一次“82 条 review 资产未经 QA 整批 Published”事故。本次为受控的窄范围临时放行，真实 QA 与人工语义验收仍列为后续验证项。
- creation 新旧资产并存，serve top-k 可能出现同意图新旧重复，属已知状态，后续按 legacy 迁移审计处置。
- 未执行 Qdrant 同步：本地 BM25 立即可覆盖新增 published 资产；dense 侧待下次同步补齐。
