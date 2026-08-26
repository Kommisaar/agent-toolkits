# AGENTS.md

本仓库是面向开发者的开发协作方法论工具集（把可复用的协作实践做成 Agent Skill，按需扩充），同时充当本地插件市场（marketplace），当前只含 `dev-toolkit` 一个插件，提供两个相互独立的 Skill：`facilitator`（分阶段访谈产出 `docs/design/` 设计文档）和 `init`（把设计协作准则以受管段落写入用户项目的 `AGENTS.md`）。仓库为纯 Markdown/JSON，无构建、测试和 lint。

## 目录结构

- `marketplace.json` 与 `.claude-plugin/marketplace.json`：marketplace 清单，两份内容一致，改动需同步。
- `plugins/dev-toolkit/`：插件本体。
  - `.claude-plugin/plugin.json` 与 `package.json`：插件元数据，版本号必须一致，发布新版时同步更新。
  - `skills/facilitator/`：`SKILL.md` 为唯一入口（保持低于 500 行），下挂 workflow、document-conventions、examples、quality-gates、phase-00～06 阶段剧本及 `templates/`。
  - `skills/init/`：`SKILL.md` 与 `agent-guidelines.md`。
- `README.md`：用户文档，其「维护」一节是修改规则的事实来源。

## 验证方式

无自动化校验，改动后自查：

- JSON 文件可解析且格式一致：`python -m json.tool marketplace.json`（对两份 marketplace 清单和插件元数据都要执行）。
- SKILL.md 的 frontmatter（name、description）完整，description 中的触发词与 README 描述一致。

## 架构边界与修改规则

- 两个 Skill 无运行时依赖：`init` 只检查目标项目内 `docs/design/README.md` 是否存在并从自身模板安装准则，不加载 facilitator 的任何文件。不要引入跨 Skill 引用。
- 每个 Skill 目录自包含，`SKILL.md` 是唯一入口；新增参考文件必须由 `SKILL.md` 直接链接，不要放孤立文件。
- Skill 目录名保持短名（`facilitator`、`init`），归属由插件命名空间 `dev-toolkit:` 识别。
- `templates/` 目录结构与产出的 `docs/design/` 镜像；改动任一模板需同步检查对应阶段剧本和 `quality-gates.md` 是否要更新。
- 准则内容只在 `skills/init/agent-guidelines.md` 维护一份：`<!-- design-guidelines:start -->` 与 `<!-- design-guidelines:end -->` 之间（含 marker）是逐字安装到用户项目的受管块。两条 marker 必须各自独占一行；块外的维护注释不得进入受管块。
- 用户文档（README）描述行为时，需与 SKILL.md 实际行为一致，改动 Skill 行为时同步 README。

## 约定

- 文档与 Skill 内容使用中文；文件内路径一律使用正斜杠。
- Commit 信息遵循 Conventional Commits：使用 feat / fix / docs / refactor / chore 等标准前缀，格式为「前缀: 中文描述」。
- 设计原则：文字是设计事实的主要载体，Mermaid 仅辅助；严格区分已确认事实、假设和开放问题；不为完整性生成没有决策价值的图。
- 注意区分：本文件是本仓库的 Agent 说明；`init` Skill 写入的是**用户项目** `AGENTS.md` 的受管段，二者无关。
