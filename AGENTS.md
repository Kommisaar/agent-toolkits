# AGENTS.md

本仓库是本地插件市场（marketplace），把可复用的开发协作实践做成 Agent 插件，按需扩充，现含一个插件：`dev-toolkit` 是个人开发工具集，含 `iter-loop` 持续迭代协调器（主 Skill、scout/builder/verifier/reviewer 四个子代理、三个命令、三套策略和七个技术栈门禁包）与 `init`（把个人编码规范以受管段落写入项目 `AGENTS.md`）。仓库为纯 Markdown/JSON/Python 脚本，无构建、测试和 lint。

## 目录结构

- `marketplace.json` 与 `.claude-plugin/marketplace.json`：marketplace 清单，两份内容一致，改动需同步。
- `plugins/dev-toolkit/`：插件本体（组件说明见仓库根 `README.md`）。
  - `.cursor-plugin/plugin.json`、`.claude-plugin/plugin.json` 与 `package.json`：插件元数据，三处 name/version 必须一致，发布新版时同步更新；`.cursor-plugin/` 保留用于 Cursor `--plugin-dir` 双目标加载。
  - `skills/init/`：`SKILL.md` 为唯一入口，`coding-guidelines.md` 为受管规范模板，`stacks/` 为技术栈专项规范（id/label/applies-to 三字段 + `## <label> 专项规范` 正文）。
  - `skills/iter-loop/`：主协调 Skill（`SKILL.md` 入口，下挂 `strategies/`、`stacks/`、`references/` 与 `scripts/state_store.py` 状态助手）。
  - `agents/`：`iter-scout`、`iter-builder`、`iter-verifier`、`iter-reviewer` 四个子代理。
  - `commands/`：`iter-status`、`iter-stop`、`iter-resume`。
  - `scripts/validate_plugin.py`：插件自带静态校验器。
- `README.md`：用户文档，其「维护」一节是修改规则的事实来源。

## 验证方式

无自动化校验，改动后自查：

- JSON 文件可解析且格式一致：`python -m json.tool marketplace.json`（对两份 marketplace 清单和插件元数据都要执行）。
- 插件改动后运行其自带校验器：`python plugins/dev-toolkit/scripts/validate_plugin.py`，并确认三处清单 name/version 一致。
- SKILL.md 与子代理、命令文件的 frontmatter（name、description）完整，description 中的触发词与 README 描述一致。

## 架构边界与修改规则

- 每个 Skill 目录自包含，`SKILL.md` 是唯一入口；新增参考文件必须由 `SKILL.md` 直接链接，不要放孤立文件。
- 个人编码规范只在 `skills/init/coding-guidelines.md` 维护一份：`<!-- user-guidelines:start -->` 与 `<!-- user-guidelines:end -->` 之间（含 marker）是逐字安装到用户项目的受管块。两条 marker 必须各自独占一行；块外说明不得进入受管块。
- init 技术栈文件（`skills/init/stacks/*.md`）只细化通用规范、不放宽、不逐字重复通用规范；新增栈按现有格式新建文件并在 SKILL.md「技术栈识别」列表登记，无需改校验器。
- Skill 之间不共享运行时文件；`init` 只读写目标项目根的 `AGENTS.md`，不加载 iter-loop 目录下的文件。
- 用户文档（README）描述行为时，需与 SKILL.md 实际行为一致，改动 Skill 行为时同步 README。

## 约定

- 文档与 Skill 内容使用中文；文件内路径一律使用正斜杠。
- Commit 信息遵循 Conventional Commits：使用 feat / fix / docs / refactor / chore 等标准前缀，格式为「前缀: 中文描述」。
- 注意区分：本文件是本仓库的 Agent 说明；`init` 写入的是**用户项目** `AGENTS.md` 的受管段，二者无关。
