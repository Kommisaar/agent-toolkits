---
name: init
description: 把用户个人编码规范以受管段落初始化或更新到当前项目的 AGENTS.md，含通用规范与按仓库证据选装的技术栈专项规范（rust、java、python、typescript、react、tauri、fastapi 等）。仅供用户显式调用（dev-toolkit:init），用于初始化 AGENTS.md、写入或更新个人编码规范；每个项目通常只运行一次，可安全重跑。
disable-model-invocation: true
---

# Init：初始化个人编码规范

一次性安装工具：把 [coding-guidelines.md](coding-guidelines.md) 的通用规范与按需选配的
[stacks/](stacks/) 技术栈专项规范装配成受管段落，逐字写入当前项目根目录的 `AGENTS.md`，
使编码 Agent 在该项目中遵循统一的个人规范。

## 技术栈识别

根据用户点名与仓库证据选择零个或多个技术栈包：

- [`java`](stacks/java.md)：Maven、Gradle 和 JVM 项目；
- [`python`](stacks/python.md)：Python 应用、库和服务；
- [`rust`](stacks/rust.md)：Cargo crate 与 workspace；
- [`typescript`](stacks/typescript.md)：TypeScript、JavaScript 和 Node.js；
- [`fastapi`](stacks/fastapi.md)：FastAPI 路由、Pydantic schema 与异步服务；
- [`react`](stacks/react.md)：React 组件、Hooks 与状态所有权；
- [`tauri`](stacks/tauri.md)：Tauri 2 桌面应用及前后端 IPC 边界。

各栈 frontmatter 的 `applies-to` 写明判定证据。用户点名了栈的直接采用；未点名时按
`applies-to` 对照仓库证据（构建清单、锁文件、依赖、目录结构）列出候选，用结构化选择
题让用户确认后再装。构建清单、锁文件与依赖声明算强证据；仅有源码扩展名算弱证据，
弱证据命中默认不装、必须用户确认。识别不出且用户未指定时，只装通用规范。

技术栈包可以组合，例如 Python 服务组合 `python` 和 `fastapi`，Tauri 项目组合
`tauri`、`typescript` 和 `rust`。蕴含的基础栈自动补全并向用户说明：`fastapi` 蕴含
`python`，`react` 蕴含 `typescript`，`tauri` 蕴含 `typescript` 与 `rust`。

## 装配规则

受管块的最终形态固定如下，栈正文整体位于两条 marker 之内：

```markdown
<!-- user-guidelines:start -->
<!-- stacks: <id 列表，按装配顺序> -->

[coding-guidelines.md 两条 user-guidelines marker 之间的内容，不含 marker 本身]

[各选中栈 `## <label> 专项规范` 正文，含二级标题]
<!-- user-guidelines:end -->
```

1. `<!-- stacks: ... -->`：记录本次栈选择，固定写在起始 marker 之后的第一行；
2. 通用规范：coding-guidelines.md 中两条 marker 之间的内容（不含 marker）；
3. 栈正文按固定顺序排列，不按用户点名顺序：基础栈（java、python、rust、
   typescript）在前，框架与集成栈（fastapi、react、tauri）在后，同类内按文件名升序。

栈文件只细化通用规范、不放宽、不逐字重复；与通用规范冲突时以通用规范为准。

## 安装规则

1. 确定项目根：单一根直接采用；多根工作区或嵌套仓库先向用户确认目标根，不猜测写入。
2. 按行读取项目根 `AGENTS.md`（不存在则视为无 marker）；marker 判定以整行精确匹配为
   准，不受 LF/CRLF 行尾差异影响。
3. 统计两条 marker 并分类处理：
   - 无 marker：文件不存在时创建（首行 `# AGENTS.md`），存在时在文件末尾追加受管块；
     文件末尾缺少换行时先补一个换行，再前置一个空行；
   - 有效受管块（两条 marker 各恰好一次、均独占一行、start 在 end 之前）：按当前选择
     整体重装配替换，marker 之外的任何内容一律不动；
   - 异常（仅出现一端、任一 marker 重复、顺序颠倒、未独占一行）：立即停止并报告具体
     位置，不修改文件，不猜测修复。
4. 重跑时栈选择的来源，按优先级：用户本次点名了栈，采用点名结果；未点名但受管块已有
   stacks 标记，沿用记录的选择并告知可点名更换；既无点名也无记录，走完整识别流程。
5. 写入保持文件原有行尾风格（LF/CRLF），不整体改写无关行。
6. 写后回读自检：重新读取文件，确认三条断言——两条 marker 各恰好一次且独占一行、受管
   块内容与预期装配逐行一致、marker 之外内容与写入前逐行一致；任一失败则用写入前的
   原内容恢复文件并报错。
7. 结果分四类：`create`（新建文件）、`append`（追加到已有文件）、`update`（替换已有
   受管块）、`unchanged`（装配结果与现有受管块逐行相同，不重写文件）。

## 输出

安装完成后报告：结果分类、写入的文件路径、受管块行数、已装栈列表；`update` 时附旧块
与新块的差异摘要（栈增减、通用规范有无变化）。同时说明两件事：

- 「业务不变量与已知坑」小节由用户在受管块之外手工维护，重跑本 Skill 不会触碰；
- 移除个人规范的方法：删除两条 marker 之间（含 marker）的内容。

结果为 `create` 或 `append`（首次安装）时，回复末尾附上下面的骨架文本供用户粘贴到
受管块之后；本 Skill 不把它写入文件：

```markdown
## 业务不变量与已知坑

### 不变量

<!-- 本系统必须永远成立的业务规则，Agent 无法从代码推断的 -->

### 真实脏输入形态

<!-- 外部数据实际长什么样：重复回调、全角字符、空数组、超长字段 -->

### 并发与时序

<!-- 竞态、幂等、顺序依赖、轮询间隔的现实 -->

### 绝对禁止的操作

<!-- 一碰就出事的操作：某个表、某条流水线、某个线上开关 -->
```

## 约束

- 仅供用户显式调用（dev-toolkit:init），不响应普通开发任务中的自动触发。
- 只读写项目根的 `AGENTS.md`；不改其他文件（栈识别只读仓库证据，不生成项目专属规则）。
- 受管块内容以通用模板和栈文件为唯一来源；要调整规范就改模板后重跑，不手工改受管块。
- 不覆盖、不重排 `AGENTS.md` 中已有的其他内容；追加位置固定为文件末尾。
