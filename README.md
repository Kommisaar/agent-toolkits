# Dev Toolkit

面向开发者的开发协作方法论工具集：把可复用的开发协作实践做成 Agent Skill，按需持续扩充。现包含两个相互独立的 Skill：一个通过阶段化访谈产出 Markdown 设计文档，一个把固定的设计纪律一次性安装进编码会话。目标是消除“开发者不知道 Agent 做了什么”的黑盒现状——让 Agent 的判断、假设和无知都落到可审查的文件上。

## 安装

本仓库同时是一个本地插件市场（marketplace）。把本仓库目录添加为 marketplace 后安装 `dev-toolkit` 插件，两个 Skill 即可使用，调用形式为 `dev-toolkit:facilitator` 和 `dev-toolkit:init`（短名 `facilitator`、`init` 同样有效）。添加本地 marketplace 的操作与此前安装 zcode-pets 时相同。推送到 GitHub 后，marketplace 来源可改为 GitHub 仓库地址，供他人一键安装。

## Skill 组成

两个 Skill 位于 `plugins/dev-toolkit/skills/` 下，目录名即 Skill 名：

### facilitator

引导式设计 Skill。通过分阶段访谈把软件想法、需求草稿或遗留系统资料整理为 `docs/design/` 下的设计文档，覆盖七个阶段：

1. 项目概览与系统边界；
2. 功能、非功能需求和业务规则；
3. 参与者与用例；
4. 领域模型、业务过程和状态；
5. 架构、组件、接口、部署和决策；
6. 模块、交互、数据与 API 详细设计；
7. 追踪、一致性和风险验证。

### init

手动运行的一次性初始化 Skill。项目存在 `docs/design/README.md` 后，将固定的设计协作准则以受管段落写入项目 `AGENTS.md`：改码先查设计、适用时携带设计编号、偏差不得静默实现、按需维护工作摘要、新需求先进设计。它不解析阶段状态或生成项目专属规则，每个项目通常只运行一次，可安全重跑。

## 使用流程

```text
设计：dev-toolkit:facilitator 分阶段访谈 → 用户逐阶段确认基线
安装：手动运行 dev-toolkit:init → 准则写入 AGENTS.md
编码：编码 Agent 每会话读取 AGENTS.md → 设计纪律在实现阶段持续生效
```

## 典型请求

- “从需求开始引导我设计这个系统。”
- “根据现有 README 和代码补齐 `docs/design/`。”
- “继续上次未完成的架构设计。”
- “检查现有设计文档从需求到详细设计是否一致。”
- “把设计准则初始化到 AGENTS.md。”

## 设计原则

- 文字是设计事实的主要载体，图表（Mermaid）用于辅助理解。
- 每轮只提出少量高价值问题；已确认事实、假设和开放问题严格区分。
- 每个阶段由用户确认后建立基线；需求变化触发受影响下游阶段的定向修订。
- 只为复杂度和风险编写详细设计，避免文档化普通样板代码。
- 两个 Skill 无运行时依赖：init 只检查项目内 `docs/design/README.md` 是否存在，并从自身固定模板安装准则，不加载 facilitator 的文件。

## 维护

- 每个 Skill 目录自包含，各自的 `SKILL.md` 是唯一入口；
- Skill 归属由插件命名空间 `dev-toolkit:` 识别，目录名保持简短（`facilitator`、`init`）；
- 设计 Skill 的 `SKILL.md` 保持简洁并低于 500 行，所有参考文件由它直接链接；
- `templates/` 结构与 `docs/design/` 保持镜像，模板改动需同步检查对应阶段剧本与质量门禁；
- 准则内容只在 `plugins/dev-toolkit/skills/init/agent-guidelines.md` 维护一份；
- 插件结构：marketplace 清单位于 `.claude-plugin/marketplace.json`，插件本体在 `plugins/dev-toolkit/`；发布新版时更新 `plugins/dev-toolkit/.claude-plugin/plugin.json` 的版本号，并与插件 `package.json` 保持一致；
- 路径使用正斜杠；新规则同时检查示例、质量门禁和阶段剧本是否需要更新。
