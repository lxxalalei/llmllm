# Mattermost Channel Creation 纵向验证

- 状态：in_progress
- 路线：[Phase 1 — 单模块纵向验证](../roadmap.md#phase-1--单模块纵向验证-in_progress)
- 所有者：llmllm 项目
- 依赖：公开可访问的 `mattermost/mattermost` 固定 ref

## 目标与非目标

目标：用一个真实、成熟的企业 IM 功能验证 `llmllm` 的长期知识漏斗是否成立：

```text
Mattermost Channel Creation Code
→ L1 Engineering Facts
→ L2 Engineering Rules
→ L3 Product Logic
→ L4 User Knowledge / FAQ
```

首个功能只覆盖公开/私有频道创建相关规则。

明确不覆盖：

- Direct Message / Group Message Channel 创建
- Channel 搜索
- Channel 归档/恢复
- Channel 重命名与完整生命周期
- Web 前端完整交互
- Mattermost 全仓库扫描
- 对 Mattermost 上游仓库进行任何修改

## 固定输入

- 仓库：`mattermost/mattermost`
- 分支：`master`
- 固定 commit：`43b2ae87e06b06abe01f9382ec26899c54c31728`
- commit 固定原因：保证本轮 L1-L4 产物可重复、可追溯，不随上游 master 漂移。

### 核心文件

- `server/channels/app/channel.go`
  - `CreateChannelWithUser`
  - `CreateChannel`
- `server/channels/api4/channel.go`
  - HTTP/API 创建入口
- `server/channels/app/channel_test.go`
  - App 层频道创建规则测试
- `server/channels/api4/channel_test.go`
  - API 层频道创建测试

后续只有在上述代码显式依赖某个 model/store 定义且无法理解当前规则时，才允许向依赖文件做最小下钻。

## 当前代码理解基线

从固定 ref 已确认至少存在以下可抽取事实，具体知识条目以 M2 正式生成结果为准：

- `CreateChannelWithUser` 拒绝 Group/Direct Channel。
- Board Channel 需走专用创建路径。
- Space Channel 有独立约束。
- 创建普通频道必须有 `TeamId`。
- 团队频道数量受到 `MaxChannelsPerTeam` 约束。
- `CreateChannelWithUser` 将创建者写入 `CreatorId`。
- 创建后会把频道加入创建者默认分类。
- 创建后会发布 `WebsocketEventChannelCreated`。
- `CreateChannel` 会清理 DisplayName/CategoryName 前后空白。
- Store 保存阶段会处理非法类型、已存在频道、频道上限等错误。
- `addMember=true` 时，创建者会作为 ChannelMember 写入，并被赋予管理员标记。
- 创建者加入频道后会记录 ChannelMemberHistory JoinEvent。
- 创建后会使创建者的频道缓存失效。
- Managed Category 是否生效取决于许可证和 Feature Flag。
- 非 Space Channel 创建后会异步触发插件 `ChannelHasBeenCreated` Hook。

这些只是用于证明首个功能的知识密度足够，不直接视为已发布的 L1/L2/L3/L4 资产。

## 修改范围

预计修改 `llmllm`：

- Go Tree-sitter parser / 通用 symbol parser 接入
- 外部源码 Source Manifest
- `Code → L1` 编译节点
- Mattermost Channel Creation 的 L1-L4 资产目录
- 来源绑定与追溯测试
- 后续角色检索/影响传播所需的最小实现

明确排除：

- 为 Mattermost 特写硬编码业务解析器
- 一次性构建全 Go 语义分析平台
- 为首个样本引入 Neo4j、Kafka、CrewAI、AutoGen 等额外基础设施

## 验收标准

### M1 — 输入冻结

- 固定仓库与 commit 可以读取。
- `llmllm` 能读取上述核心源码文件。
- 能识别 Go 文件中的函数/方法 symbol，至少包括 `CreateChannelWithUser` 和 `CreateChannel`。
- 明确 Mattermost 基线测试命令及运行环境依赖。

候选基线测试：

```bash
cd server
go test ./channels/app -run 'TestCreateChannel'
go test ./channels/api4 -run 'TestCreateChannel'
```

候选命令必须在实际运行后记录结果；若依赖数据库或 Mattermost 测试环境，则记录依赖和可重复启动方式，不以“命令存在”冒充“测试通过”。

### M2 — Code → L4

从固定 ref 形成正式长期产物：

- 10~30 个 L1 Engineering Facts
- 3~10 个 L2 Engineering Rules
- 3~10 个 L3 Product Logic
- 10~30 个 L4 FAQ / 用户知识

每个 L1 必须绑定具体 source 文件、ref 与 symbol；L2-L4 必须保留 `derived_from`。

### M3 — 角色与追溯

- 普通用户只能消费 Published L3/L4。
- 产品/测试可从 L3 下钻 L2。
- 开发可从 L2/L1 定位到 Mattermost 固定 ref 代码。
- 任一 L4 可以沿关系链追溯到至少一个代码 source。

### M4 — 变化传播

使用本地/测试 fixture 制造一个可控的 Channel Creation 规则变化，例如频道上限、类型限制或创建后行为发生变化：

- 能定位受影响 L1。
- 能沿关系找到受影响 L2/L3/L4。
- 受影响知识进入 stale/review 状态。
- 不修改 Mattermost 上游仓库。

## 里程碑

- M1 — in_progress — Mattermost 来源、固定 ref、功能边界和主要入口已确定；待 `llmllm` 实际读取 Go symbol 并执行/确认基线测试环境。
- M2 — pending — 生成并审核正式 L1-L4。
- M3 — pending — 验证角色检索和全链追溯。
- M4 — pending — 验证可控变更的影响传播。

## 决策记录

### 选择 Mattermost

Mattermost 是成熟的企业协作 IM，频道、成员、权限、消息等领域对象明确，适合验证企业产品知识抽象，不需要人为构造 demo 业务。

### 首个功能选择 Channel Creation

不选择整个 Channel 模块。频道创建同时具备 API、应用层规则、Store 错误、成员关系、事件、插件、配置和许可证约束，知识密度足够，同时范围仍然可控。

### 固定 commit 而不是跟随 master

长期知识资产必须有稳定证据来源。首次验证固定 commit；未来增量编译阶段再验证上游 ref 变化如何传播。

## 验证证据

当前已验证：

- GitHub 可读取 `mattermost/mattermost`。
- `master` 在选定时指向 `43b2ae87e06b06abe01f9382ec26899c54c31728`。
- 已读取 `server/channels/app/channel.go` 中的 `CreateChannelWithUser`、`CreateChannel` 及其关键后续逻辑。
- 已定位 App/API 层 `TestCreateChannel` 测试文件。

当前未验证：

- Mattermost 测试命令在本地环境的实际执行结果。
- `llmllm` 当前 Tree-sitter 实现尚不支持 Go。
- 正式 L1-L4 尚未生成。

## 完成记录

待 M4 完成后补充，并同步更新 `docs/roadmap.md`。
