# Mattermost Channel Creation 纵向验证

- 状态：in_progress
- 路线：[Phase 1 — 单模块纵向验证](../roadmap.md#phase-1--单模块纵向验证-in_progress)
- 所有者：llmllm 项目
- 依赖：公开可访问的 Mattermost 固定 ref；真实模型运行需要 LLM 凭据

## 目标与非目标

目标：用真实企业 IM 功能验证：

```text
Mattermost Channel Creation Code
→ L1 Engineering Facts
→ L2 Engineering Rules
→ L3 Product Logic
→ L4 User Knowledge / FAQ
```

只覆盖公开/私有团队频道创建；不扩展 Direct/Group、搜索、归档、完整生命周期、完整前端和全仓库扫描。

## 固定输入

- 仓库：`mattermost/mattermost`
- 固定 commit：`43b2ae87e06b06abe01f9382ec26899c54c31728`
- 核心文件：`server/channels/app/channel.go`
- 核心 symbol：`CreateChannelWithUser`、`CreateChannel`
- API：`server/channels/api4/channel.go`
- 测试：`server/channels/app/channel_test.go`、`server/channels/api4/channel_test.go`

## 当前实现结果

### M1 输入与解析

已完成：

- 固定 repo/ref/file/symbol。
- Go Tree-sitter parser，与 Python parser 共用 Symbol 数据结构。
- symbol 保留 declaration source、起止行。
- Compiler Preview 可解析 Go/Python `content`。
- CI 已验证 Go parser 和 Compiler source analysis。

Mattermost 自身以下候选命令尚未实际运行：

```bash
cd server
go test ./channels/app -run 'TestCreateChannel'
go test ./channels/api4 -run 'TestCreateChannel'
```

不描述为测试通过。

### M2 长期知识资产与生成器

人工基准集：

- 12 个 L1 Engineering Facts，绑定固定 commit/file/symbol。
- 4 个 L2 Engineering Rules。
- 3 个 L3 Product Logic，全部 `review`。
- 6 个 L4 FAQ，全部 `draft`。

真实 `Code → L1` 生成能力：

- OpenAI Responses API + JSON Schema Structured Outputs。
- 模型只返回 `key / symbol / title / statement`。
- `symbol` 必须属于 parser 实际提取的 symbol，否则生成失败。
- repo/ref/commit/file/start_line/end_line 全由程序生成，模型不能伪造来源。
- 重复 knowledge ID 直接报错。
- 生成结果固定为 L1 `draft`，不会自动升级为产品规则。
- 未配置 provider 时 Compiler 明确记录 `l1_skipped_no_provider`。
- L2/L3/L4 自动生成尚未实现时明确记录 `*_not_implemented`。

真实运行 harness：

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=<支持 Structured Outputs 的模型>
export LLM_API_KEY=<your key>
python scripts/generate_mattermost_l1.py /path/to/mattermost --output /tmp/mattermost-l1.json
```

脚本要求 Mattermost checkout 正好位于固定 commit，目标源码不能有本地修改，并且必须找到两个目标 symbol。

### Lineage

已实现 Markdown/YAML 资产加载、稳定 ID、`trace_lineage`、`trace_sources` 以及 Knowledge Item/Lineage API。测试已验证 FAQ 可追溯到固定 Mattermost `CreateChannelWithUser`。

## 里程碑

### M1 — completed

- [x] 固定仓库、commit、模块和 symbol。
- [x] Go function/method symbol 解析。
- [x] Compiler 接收 Go source content。
- [x] 外部 Mattermost 测试命令与未验证状态明确记录。

### M2 — completed

- [x] 12 个 L1 人工基准事实。
- [x] 4 个 L2。
- [x] 3 个 L3 review 草稿。
- [x] 10~30 个 L4：Mattermost 达 10 个（2026-09-05：发布 4 + 新增 4，8 published / 2 draft）。
- [x] 真实 `Code → L1` 生成器代码。
- [x] 固定 Mattermost 本地生成 harness。
- [x] 使用真实 API 凭据运行 Mattermost → L1（2026-09-05，见验证记录）。
- [x] 将模型结果与 12 条人工基准做质量对比（2026-09-05，见验证记录）。
- [x] 产品审核并发布至少一条 L3，再派生可发布 L4（2026-09-05：批准发布 `team_channel`；派生发布 limit / creator_auto_join / default_category / join_message 4 条 L4）。

### M3 — completed

- [x] 普通用户只能消费 Published L3/L4（role=user 门控 + 404 防枚举）。
- [x] 产品/测试可从 L3 下钻 L2（drill API；test 另有 L1 资产授权）。
- [x] 开发可从 L2/L1 定位固定 ref 代码（SourceBinding repo/commit/file/symbol 经 API 暴露）。
- [x] L4 可沿 lineage 追溯到代码 source。

### M4 — pending

- [ ] 定位受影响 L1。
- [ ] 沿关系找到受影响 L2/L3/L4。
- [ ] 受影响知识进入 outdated/review 状态。

## 下一实施目标

M2（真实运行/基准对比/产品审核发布/补足 L4）与 M3（角色消费边界）已完成（2026-09-05）。下一步 M4：

- 准备一个可控代码变更样本（固定 commit 前/后），验证：changed symbol → 定位受影响 L1 → 沿关系找到受影响 L2/L3/L4 → 驱动进入 outdated/review 状态。

遗留风险（进入 M4 前可先处理，不阻塞）：两次真实运行事实切分数 17/27 不稳定且输出英文，入库前需固定切分/语言策略；27 条生成预览未逐条人工复核。

## 验证记录

- 真实 `Code → L1` 运行 1（2026-09-05，修复前 driver 复刻）：17 条 L1 `draft`，绑定全部正确；Python 3.14 曾因未关闭 AsyncOpenAI 客户端在 asyncio 收尾访问违例崩溃（0xC0000005），Python 3.12 + 显式 close 正常 → 触发 harness 修复。
- 真实 `Code → L1` 运行 2（2026-09-05，官方脚本修复后）：`python scripts/generate_mattermost_l1.py <mattermost checkout> --output .../generated-l1-official.json`，Python 3.12.13 venv，exit 0，27 条 L1 `draft`：绑定 100% 通过（0 bad）、id 无重复，CreateChannelWithUser 11 / CreateChannel 16。
- 对比方法：概念级人工映射 + 关键字核对（模型输出英文、人工基准中文）。结果：12/12 概念覆盖，无重复，无错误归因；default-category / join-message / websocket-event 被合并进一条综合事实（粒度变粗），type-routing 被拆为 3 条；4 条超出基准的新事实待人工复核。
- 端点/模型：OpenAI 兼容 Responses API（本机 Codex provider `qianji`，`OPENAI_BASE_URL` 见 README）；模型 `DS/DeepSeek-V4-Flash`；凭据不写入仓库与报告。
- 原始产物：`.scratch/run-mattermost-l1/`（generated-l1.json、generated-l1-official.json、report-2026-09-05.md、verification-summary.json）。
- 未覆盖：Mattermost 自身 `go test` 未实际执行；27 条未逐条人工复核；L3 审核发布未进行；两次运行事实切分数不一致（17/27），切分粒度策略未定。

- Go parser / Compiler Go source analysis：CI 通过。
- L1 generator source-binding 单元测试：CI 通过。
- KnowledgeCatalog 首次测试真实失败，暴露 Markdown title 与 schema 不一致；明确标题规则后 CI 通过。
- Lineage API：CI 通过。
- OpenAI provider 使用 Responses API JSON Schema Structured Outputs；CI 只验证代码与纯逻辑，不执行付费外部调用。

## 完成记录

待 M4 完成后补充，并同步更新 `docs/roadmap.md`。
