---
id: typescript
label: JavaScript / TypeScript（含 Node.js）
applies-to: 仓库含 package.json、tsconfig.json，或以 *.ts、*.js、*.mts 源码为主
---

## JavaScript / TypeScript 专项规范

### 模块与依赖边界

- 一个类、组件或模块一个文件；目录按领域划分，类型定义跟随所属领域文件。
- 禁止 index.ts 大杂烩转出口；仅公共 API 入口允许统一导出。

### 类型、数据与接口契约

- TypeScript 开 strict；模块内部实现默认不导出，导出即 API。
- 禁止 any；外部未知数据用 unknown 加类型收窄。
- `@ts-expect-error` 必须写原因与移除条件；禁止无解释的 `@ts-ignore`。

### 状态、并发与资源生命周期

- Promise 错误必须处理或显式上抛；禁止无人 await 的孤儿 Promise。
- 订阅、定时器、事件监听在所属作用域结束时清理；进程级句柄显式关闭。
- 异步竞态用取消标记或 AbortController 收敛，禁止靠时序碰运气。

### 错误、安全与可观测性

- 自定义 Error 子类携带上下文；catch 后禁止返回默认值装成功。
- 日志统一走 logger，禁止裸 console（一次性脚本除外）。

### 测试与可判定验收

- 类型检查、单测全过。

### 反模式与替代方案

- 禁止 `?.` 链式防御替代真实判空责任，改为显式收窄。
- 禁止 as 断言绕过类型检查，用收窄或修正类型定义。
- 禁止为兼容两种形态扩散联合类型，先统一输入。
