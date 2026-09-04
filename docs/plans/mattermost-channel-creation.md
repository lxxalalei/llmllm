# Mattermost Channel Creation 纵向验证

- 状态：in_progress
- 路线：[Phase 1 — 单模块纵向验证](../roadmap.md#phase-1--单模块纵向验证-in_progress)
- 所有者：llmllm 项目
- 依赖：公开可访问的 `mattermost/mattermost` 固定 ref；M2 自动生成阶段需要真实 LLM Provider

## 目标与非目标

目标：用真实企业 IM 功能验证长期知识漏斗：

```text
Mattermost Channel Creation Code
→ L1 Engineering Facts
→ L2 Engineering Rules
→ L3 Product Logic
→ L4 User Knowledge / FAQ
```

只覆盖公开/私有团队频道创建。明确不覆盖 Direct/Group、搜索、归档/恢复、完整生命周期、完整前端和全仓库扫描。

## 固定输入

- 仓库：`mattermost/mattermost`
- 固定 commit：`43b2ae87e06b06abe01f9382ec26899c54c31728`
- 核心文件：`server/channels/app/channel.go`
- 核心 symbol：`CreateChannelWithUser`、`CreateChannel`
- API：`server/channels/api4/channel.go`
- 测试：`server/channels/app/channel_test.go`、`server/channels/api4/channel_test.go`

固定 commit 用于保证 L1-L4 可重复和可追溯；增量编译阶段再验证上游变化传播。

## 当前实现结果

### M1 输入与解析

已完成：

- 固定 repo/ref/file/symbol。
- 新增 Go Tree-sitter parser，并与 Python parser 共用 `Symbol` 数据结构。
- symbol 保留 declaration source、起止行。
- Compiler Preview 可接收真实 Go/Python `content` 并输出 symbol。
- CI 已验证 Go parser 和 Compiler Go source analysis。

未验证：Mattermost 自身候选测试命令尚未在当前执行环境运行：

```bash
cd server
go test ./channels/app -run 'TestCreateChannel'
go test ./channels/api4 -run 'TestCreateChannel'
```

这项只记录为外部验证缺口，不描述为测试通过。

### M2 长期知识资产

当前人工基准集：

- 12 个 L1 Engineering Facts，全部绑定 Mattermost 固定 commit/file/symbol。
- 4 个 L2 Engineering Rules，保留 `derived_from`。
- 3 个 L3 Product Logic，全部 `status: review`。
- 6 个 L4 FAQ，全部 `status: draft`。

当前 L3/L4 不发布给普通用户，因为代码实现只是证据，不自动等于产品确认口径。

这些资产的作用是作为后续自动生成器的质量基准，不应继续靠人工扩充来代替 `Code → L1` 自动化。

### Lineage

已实现：

- `KnowledgeCatalog.from_directory`
- 稳定 knowledge ID 校验
- Markdown + YAML Frontmatter 加载
- frontmatter `title` 或 Markdown H1 标题规则
- `trace_lineage`
- `trace_sources`
- `GET /api/v1/knowledge/{knowledge_id}`
- `GET /api/v1/knowledge/{knowledge_id}/lineage`

已通过测试验证 `faq.mattermost.channel.create.limit` 可以递归追溯到 Mattermost 固定 commit 的 `CreateChannelWithUser`。

## 验收标准

### M1 — 输入冻结 (`completed`)

- [x] 固定仓库、commit、模块和 symbol。
- [x] `llmllm` 支持 Go method/function symbol 解析。
- [x] Compiler 可接收 Go source content。
- [x] Mattermost 基线测试命令和未验证状态已明确记录。

### M2 — Code → L4 (`in_progress`)

- [x] 10~30 个真实 L1 基准事实：当前 12 个。
- [x] 3~10 个 L2：当前 4 个。
- [x] 3~10 个 L3：当前 3 个，待产品审核。
- [ ] 10~30 个 L4：当前 6 个。
- [ ] `Code → L1` 由真实生成器完成，而不是人工编写。
- [ ] 产品审核并发布至少一条 L3，再由其派生可发布 L4。

### M3 — 角色与追溯 (`pending`)

- [ ] 普通用户只能消费 Published L3/L4。
- [ ] 产品/测试可从 L3 下钻 L2。
- [ ] 开发可从 L2/L1 定位固定 ref 代码。
- [x] L4 可沿 lineage 追溯到代码 source。

### M4 — 变化传播 (`pending`)

使用本地 fixture 制造频道创建规则变化，不修改 Mattermost 上游：

- [ ] 定位受影响 L1。
- [ ] 沿关系找到受影响 L2/L3/L4。
- [ ] 受影响知识进入 outdated/review 状态。

## 下一实施目标

实现真实 `Code → L1` 生成器：

1. 输入为 parser 提取的 Mattermost symbol source + SourceBinding。
2. 调用真实 LLM Provider 输出结构化 L1 `KnowledgeItem` 列表。
3. 生成结果必须保持 `draft`，不能自动上升为产品规则。
4. 与现有 12 条人工基准事实对比覆盖率、重复率和明显错误。
5. 只有该闭环成立后才继续自动化 L1 → L2。

不创建 Mattermost 专用 if/else 规则提取器，不用硬编码把当前 12 条答案吐出来。

## 验证记录

- 首次 Go parser/真实 L1 提交：CI 通过。
- 首次 KnowledgeCatalog 测试：失败，真实暴露 Markdown 标题与 `KnowledgeItem.title` schema 不一致。
- 修复：明确使用 frontmatter `title` 或 Markdown H1，缺失时直接报错；修复后 CI 通过。
- Lineage API 已加入测试，最新 CI 通过。

## 完成记录

待 M4 完成后补充，并同步更新 `docs/roadmap.md`。
