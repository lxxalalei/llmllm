# Mattermost Channel Membership 真实模型编译审核

- 日期：2026-09-06
- 上游 commit：`b3946ef5e2b85a27d365af2592cf1262de6a665e`
- Scope：`config/knowledge_scopes/mattermost-channel-membership.json`
- 模型：DeepSeek OpenAI-compatible Responses API，Structured Outputs，`reasoning.effort=none`
- 首轮 preview：`/tmp/mattermost-channel-membership-preview.json`，SHA-256 `b86c8e3bfae7aaeb43df542e614b1e3c241a4a71022f58c1f2d11a116fdb5304`
- 收紧后 preview：`/tmp/mattermost-channel-membership-preview-v4.json`，SHA-256 `eb405769ad1f22b1220c35023777bb1b749a23a7f425e641ea512f320315a12e`
- 发布状态：未发布，未写入 canonical knowledge / Qdrant

## 运行结果

- 输入：4 个 source file，12 个 symbol。
- 输出：67 条 L1，19 条 L2，0 条 L3 review candidate。
- 结构校验：通过。L1/L2 ID 全局唯一；层级、状态、repo/commit/file/symbol/line 绑定完整；L2 `derived_from` 均指向本次 L1。
- Unsupported fact：人工逐条复核未发现明确无源码支持的事实。
- Wrong attribution：未发现。

## 收紧迭代

| 迭代 | 模型 | 证据单元 | L1 | L2 | 结果 |
| --- | --- | ---: | ---: | ---: | --- |
| v1 | DeepSeek Flash | 12 | 67 | 19 | 链路通过，粒度过细，L2 抽象不足 |
| v2 | DeepSeek Flash | 13 | 49 | 15 | 加入 route range，重复减少，仍有语义扩大 |
| v3 | DeepSeek Flash | 13 | 46 | 10 | 数量收紧，但模型漏掉 `InitChannel` route 事实 |
| v4 | DeepSeek Pro | 13 | 49 | 10 | 全部结构门禁通过，语义质量仍未达发布标准 |

本轮新增了可控 source range，将 `InitChannel:109` 作为真实 SourceBinding 单独送模型；L1 按最多 4 个 symbol 分块，每个选定 symbol 必须至少有 1 条事实且每 symbol 不超过 12 条；L2 硬限制为最多 10 条。不满足时显式失败，不产出残缺 preview。

## 基线对照

人工基线原第 20 条与固定 commit 的源码冲突，已根据 `server/channels/app/channel.go:addUserToChannel` 修正：`SaveMember` 后确实直接调用 `ChannelMemberHistory.LogJoinEvent`。模型对此项的输出有直接代码证据，不是幻觉。

首轮修正后的 25 个 L1 核心概念中：

- 完整覆盖 21 项。
- 部分覆盖 3 项：`UserRequestorID` 的显式解析语义、`PostRootID` 与 AddToChannel system post 的端到端关联、主动离开与被移除使用不同 system-post type。
- 遗漏 1 项：POST route 由 `APISessionRequired(addChannelMember)` 注册的登录会话约束。该证据位于 route initialization，不在当前送模型的 12 个 symbol 内。

9 个 L2 基线主题均能在生成结果中找到语义证据，但多层门控、加入副作用和 actor/requestor 语义被拆散到多条规则，没有形成稳定的跨 L1 工程抽象。

收紧后 v4 的 25 个 L1 核心概念为 23 项完整覆盖、2 项部分覆盖（`UserRequestorID` 解析与 `PostRootID` 端到端传递）。route 会话约束已补齐。但 L2 只稳定覆盖 9 个基线主题中的 team integrity、group constraint、discoverable self-add 和 guard 四类；完整加入副作用、移除依赖清理、双路移除通知和 actor/requestor 未进入最终 10 条。

## 质量问题

1. L1 粒度偏细。`IsDiscoverableSelfAddBlocked` 被分成 5 条单条件事实加 1 条组合事实，存在明显重复。
2. L2 数量偏多且部分停留在 HTTP 机制层，例如参数校验、响应状态码、handler 委派和批处理错误；这些更适合保留为 L1，不应占用主要 L2 规则。
3. L2 缺少“membership 是 HTTP permission → team/group/policy/guard → persistence → side effects”的综合规则，现有输出主要是对 L1 的分组改写。
4. 登录 route 约束的遗漏来自 scope 结构缺口，不是单纯提示词问题。
5. v4 仍有 L1 语义重复/措辞不严谨：discoverable self-add 的 false/true 条件被拆成两条重叠事实，remove channel type 的内容只列 Direct/Group 而标题表达为仅允许 Open/Private。
6. v4 L2 `plugin_hook_fail_mode_contract` 将源码中“先 non-guard、后 guard”反写为 non-guard 在 guard 之后，属于 unsupported ordering，必须拒绝发布。

## 验收结论

本次真实模型调用、Structured Outputs、SourceBinding 和 L2 lineage 链路已跑通；收紧后 v4 的 49 L1 / 10 L2 通过全部结构门禁。但语义复核仍发现重复、遗漏和 unsupported ordering，因此停在 preview/review，不进入 Publish、Qdrant 和 QA。

下一验收项：在 L1/L2 生成之后增加语义 Review/Repair 阶段，以 source 与 `derived_from` 为唯一证据删除重复、纠正 unsupported clause，并对基线主题做显式 coverage gate；通过后再决定是否发布。
