# Agent Toolkits

本地插件市场（marketplace），把可复用的开发协作实践做成 Agent 插件，按需持续扩充。现含一个插件 `dev-toolkit`——个人开发工具集：`iter-loop` 在用户授权的预算内用后台子代理持续发现、实现、验证、审查并线性合并代码改进；`init` 把个人编码规范一次注入项目 `AGENTS.md`、处处生效。目标是消除“开发者不知道 Agent 做了什么”的黑盒现状——让 Agent 的判断、假设和无知都落到可审查的文件上。

## 安装

本仓库同时是一个本地插件市场（marketplace）。把本仓库目录添加为 marketplace 后安装 `dev-toolkit` 插件，即可使用：

- `init` Skill 与 `iter-loop` Skill（调用形式 `dev-toolkit:init`、`dev-toolkit:iter-loop`，短名同样有效）；
- `iter-scout` / `iter-builder` / `iter-verifier` / `iter-reviewer` 四个子代理；
- `/iter-status`、`/iter-stop`、`/iter-resume` 三个命令。

`iter-loop` 运行时需要目标机器已安装 Git 和 Python 3.10+。

## init：初始化个人编码规范

一次性安装工具，把插件内 `skills/init/coding-guidelines.md` 的通用规范与按需选装的技术栈专项规范装配成受管段落，逐字写入当前项目根的 `AGENTS.md`。通用规范涵盖：代码组织（严格分层、一个类一个文件）、简单性（禁止无必要抽象与过早提取）、错误处理纪律（禁止吞错、防御需有证据）、注释与文档（注释解释原因、过期注释视为缺陷）、测试与验收（验收必须可判定）。技术栈规范位于 `skills/init/stacks/`（现含 rust、java、python、typescript、react、tauri、fastapi），init 按 `applies-to` 对照仓库证据列出候选、用户确认后装入选中栈，可多选组合，蕴含的基础栈自动补全（fastapi 蕴含 python，react 蕴含 typescript，tauri 蕴含 typescript 与 rust）。每个项目通常只运行一次，可安全重跑：未点名新栈时沿用受管块内 stacks 标记记录的上次选择，装配结果不变则不重写文件；受管块 marker 异常（缺失一端、重复、错位、未独占一行）时报错停止、不修改文件；重装或更新不触碰项目已有内容，也不触碰受管块之外手工补充的「业务不变量与已知坑」小节（首次安装时在回复中附送该小节的粘贴版骨架，不写入文件）。

## iter-loop：持续迭代协调器

`iter-loop` 在用户明确授权的预算内（截止时间、最大任务数或“直到我叫停”）循环执行：发现候选 → 选择任务 → worktree 隔离派发 → 审查验证 → ff-only 线性合并 → 滚动补位 → 汇报。主 Skill 是协调器，合并、rebase、worktree 清理和最终决策只归协调器所有。

组件构成：

- 主 Skill `iter-loop`：显式启动的协调器，负责策略选择、运行卡、并发、Git 集成和验收；
- 四个后台子代理：`iter-scout`（只读审计生成候选）、`iter-builder`（在指定 worktree 实现单任务）、`iter-verifier`（rebase 后独立执行完整门禁）、`iter-reviewer`（只读审查最终 diff 与证据）；
- 三套运行策略：`conservative`（稳定性优先）、`balanced`（质量与路线图均衡）、`feature`（围绕明确授权的功能目标），策略只填补默认值，不能扩大授权；
- 七个可组合技术栈门禁包：TypeScript、前端 Web、Python、Rust、Java/JVM、React、Tauri 2；
- 三个命令：`/iter-status`（只读核对）、`/iter-stop`（安全收尾或立即停止）、`/iter-resume`（对账后恢复）。

运行状态保存在目标仓库的 `.auto-iter/runs/`（clone 本地、不提交），只有协调器可写。安全边界包括：不处理用户未提交改动、不自动 push/发布/部署、高风险变更（数据迁移、认证授权、破坏性接口等）必须暂停确认、不信任代理自报结果而以实际 diff 和门禁证据为准。该插件为单会话设计，会话结束后后台代理不再运行，恢复须由用户显式调用 `/iter-resume`。

worktree 池：唯一的任务派发模式。池目录默认在主树同级 `<仓库名>-iter/pool/`（天然同盘），项目 `AGENTS.md` 可声明池目录与池位数覆盖；池位跨任务复用 `node_modules` 与工具缓存，任务标识只体现在分支名。池位与依赖跨 run 保留：run 结束只注销台账登记并留痕，恢复与新 run 优先接管现存池位，物理移除仅在用户明确要求或确认不再迭代时执行。

## 使用流程

```text
初始化：dev-toolkit:init → 个人编码规范写入项目 AGENTS.md（每项目一次）
迭代：显式输入 /iter-loop → 授权预算内持续派发、验证并合并小步改进
监控：/iter-status 只读核对 → /iter-stop 安全收尾或立即停止
恢复：会话中断后 /iter-resume → 对账 Git 现场后续跑
```

## 典型请求

- “/dev-toolkit:init 把这个项目的 AGENTS.md 初始化一下。”
- “/dev-toolkit:init 更新一下 AGENTS.md 里的个人规范。”
- “/iter-loop 以稳定性和测试补强为主，最多完成 3 个低风险任务。”
- “/iter-loop 围绕已批准的功能目标推进一个纵向切片。”
- “/iter-status 看一下当前迭代运行到哪了。”
- “/iter-stop 安全收尾，别再派新任务。”
- “上次会话断了，/iter-resume 接着跑。”

## 维护

- 插件结构：marketplace 清单有两份（根目录 `marketplace.json` 与 `.claude-plugin/marketplace.json`），内容一致，改动需同步；插件本体在 `plugins/dev-toolkit/`，新增插件时在两份清单中登记。
- `dev-toolkit` 的 name/version 在三处清单保持一致：`.cursor-plugin/plugin.json`（Cursor 加载用，保留双目标兼容）、`.claude-plugin/plugin.json` 与 `package.json`；修改后运行 `python plugins/dev-toolkit/scripts/validate_plugin.py` 做静态校验。
- 个人编码规范只在 `plugins/dev-toolkit/skills/init/coding-guidelines.md` 维护一份：两条 `user-guidelines` marker 之间（含 marker）是逐字安装到用户项目的受管块；要改规范就改模板后让用户重跑 init，不手工改目标项目里的受管块。
- init 技术栈文件位于 `plugins/dev-toolkit/skills/init/stacks/`：frontmatter 固定 `id`（与文件名一致）、`label`、`applies-to` 三字段，正文为 `## <label> 专项规范` 下固定顺序的六节骨架（模块与依赖边界、类型数据与接口契约、状态并发与资源生命周期、错误安全与可观测性、测试与可判定验收、反模式与替代方案），无内容的节可省略、顺序不得打乱；栈文件只细化通用规范、不放宽、不逐字重复，与通用规范冲突时以通用规范为准；新增栈无需改校验器，但需在 SKILL.md「技术栈识别」列表登记。
- 用户文档描述行为时，需与插件 `SKILL.md` 实际行为一致，改动插件行为时同步 README。
- 路径使用正斜杠；新规则同时检查对应策略、技术栈包和命令文档是否需要更新。
