---
id: typescript
label: TypeScript 与 Node.js
applies-to: TypeScript、JavaScript、Node.js 和相关 monorepo
---

# TypeScript 与 Node.js

## 识别

出现以下证据时应用本包：

- `package.json`；
- `tsconfig.json` 或 `tsconfig.*.json`；
- `.ts`、`.tsx`、`.mts`、`.cts` 文件；
- pnpm、npm、Yarn、Bun、Nx、Turborepo 等工作区配置。

只有 `package.json` 且项目不是 JavaScript/TypeScript 运行时工具时，不要仅凭文件名误判。

## 工具链

1. 优先读取 `package.json#packageManager`、仓库文档和 CI。
2. 其次根据唯一锁文件选择包管理器：
   - `pnpm-lock.yaml` → pnpm；
   - `yarn.lock` → Yarn；
   - `package-lock.json` 或 `npm-shrinkwrap.json` → npm；
   - `bun.lock` 或 `bun.lockb` → Bun。
3. 多个锁文件或声明冲突时暂停，不混用包管理器。
4. 使用项目已有脚本和 workspace 过滤能力，不自行发明另一套命令。
5. worktree 缺少依赖时只使用项目声明的安装方式；不要手工链接或复制 `node_modules`。

## 门禁发现

从根 `package.json`、子包脚本、CI 和任务编排配置中映射：

- 格式检查：`format:check`、Prettier、Biome 等；
- lint：ESLint、Biome 或项目脚本；
- 类型检查：`typecheck`、`tsc --noEmit` 或构建型 tsconfig；
- 单元/组件测试：Vitest、Jest、Node test runner 等；
- 集成/E2E：项目已有脚本；
- 构建：`build`、bundler 或 monorepo pipeline。

不要因为测试通过而跳过类型检查或构建。若项目没有某类门禁，记录“未配置”，不要临时
引入工具。

## 执行策略

- Builder 优先运行受影响 package 的任务级测试、lint 和类型检查。
- Verifier 在 rebase 后按项目定义运行完整 workspace 门禁。
- monorepo 可先使用受影响过滤加快反馈，但合并前完整范围由仓库 CI 契约决定。
- 测试 watch 模式不得用于门禁；使用一次性、可退出模式。
- CI 与本地脚本参数不一致时，以仓库约定和 CI 为准并记录差异。

## 生成物与污染

重点检查：

- 锁文件；
- `dist`、`build`、`.next`、`.nuxt`、`.svelte-kit`；
- coverage、测试报告和快照；
- 代码生成的类型、客户端、bindings 或 schema 输出；
- `.turbo`、`.nx`、`.eslintcache`、`*.tsbuildinfo`。

缓存和构建目录只有在项目明确忽略且任务包允许时才视为预期。快照、锁文件和已跟踪生成物
发生变化必须作为真实 diff 审查，不得由 Verifier 自动更新或还原。

## 常见风险

- ESM/CJS、Node 版本和条件导出差异；
- 浏览器端与服务端默认值漂移；
- 类型声明通过但运行时 schema 不一致；
- workspace 包之间引用旧构建产物；
- 时区、浮点、并发和异步错误未被测试覆盖。

报告中注明实际包管理器、Node/运行时约束、受影响 workspace、完整门禁命令和生成物变化。
