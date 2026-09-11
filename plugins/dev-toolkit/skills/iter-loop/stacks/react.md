---
id: react
label: React
applies-to: React 组件、Hooks、客户端渲染、SSR 与 React 前端测试
---

# React

## 组合方式

React 是框架叠加包，不替代通用 Web 或语言包：

- 通常组合 `typescript` 和 `frontend-web`；
- Tauri React 项目组合 `tauri`、`rust`、`typescript`、`frontend-web`、`react`；
- 使用 Next.js、Remix 等上层框架时，继续遵守其项目约定；本包不假设特定全栈框架。

## 识别

出现以下证据时应用本包：

- `package.json` 依赖 `react` 与对应 renderer，例如 `react-dom`；
- `.jsx`、`.tsx` React 组件或 JSX runtime 配置；
- React Router、Testing Library、React Hooks ESLint 或 React 构建插件；
- 客户端入口使用 `createRoot`、hydrate 或项目框架的 React adapter。

从 package manifest 和锁文件确认实际 React 主版本。不要把 Preact、Solid 或其他 JSX
框架仅凭 `.tsx` 文件误判为 React，也不要向旧版本套用新版本 API。

## 组件与 Hooks

审查以下不变量：

- 组件和 Hook 在渲染阶段保持纯函数，不产生网络、文件、订阅或全局写入；
- Hook 只在 React 组件或自定义 Hook 顶层调用，不放入条件、循环和普通回调；
- Effect 只用于同步外部系统，依赖项与实际读取值一致；
- Effect、ref callback、事件订阅、timer 和 Tauri listener 有对称清理；
- StrictMode 下重复 render、Effect setup/cleanup 和 ref callback 不造成重复副作用；
- state 更新使用正确的函数式形式，避免闭包读取旧值；
- list key 稳定并表示业务身份，不用易变索引掩盖状态错位；
- 派生数据优先在 render 或 memo 中计算，不用 Effect 制造双份状态；
- Context、reducer 和外部 store 的订阅范围与更新粒度清晰。

遵守项目启用的 `eslint-plugin-react-hooks` 规则，包括 Rules of Hooks 和依赖检查。不得通过
禁用规则、删除依赖或添加无依据的 lint 忽略解决问题。

## 异步与并发行为

- 异步 Effect 处理取消、竞态、组件卸载和响应乱序；
- loading、empty、error、retry 与权限状态均可判定；
- Suspense boundary 有稳定 fallback，并考虑重挂载和状态重置；
- transition、deferred value 和乐观更新只有在项目实际使用时审查；
- render 中不依赖调用次数、执行顺序或开发模式只执行一次的假设；
- 错误边界、路由切换和后台请求不会泄漏 listener、timer 或 AbortController。

## SSR 与 Hydration

仅在项目存在 SSR、预渲染或 hydration 时应用：

- 服务端与客户端首屏输出保持确定性；
- render 不直接读取仅浏览器存在的全局对象；
- 时间、随机值、locale、媒体查询和持久化状态不会制造 hydration 差异；
- Suspense、数据缓存和客户端边界符合上层框架约定；
- 浏览器无 hydration warning 不等于服务端路径已覆盖，必须结合构建或 SSR 测试。

Next.js、Remix 等框架的 Server Components、路由、数据加载和缓存规则应由独立框架包或
仓库约定提供，不在本包中泛化。

## 测试

- 优先通过用户可观察行为测试组件，不锁定内部 state 或实现细节；
- 使用项目已有的 Testing Library、Vitest、Jest 或浏览器工具，不临时混入另一套框架；
- 触发更新后按项目工具正确等待异步 UI；React 底层测试使用 `act` 边界；
- 覆盖 props、交互、错误、清理、路由或 Context 集成；
- StrictMode 相关缺陷应在启用 StrictMode 的测试或开发路径中复现；
- mock 必须保留真实模块的异步、错误和清理语义；
- 快照仅作为补充，不用大面积快照代替行为断言，也不自动接受更新。

## Tauri React 注意事项

- `invoke`、events 和 channels 与 Rust command 契约保持一致；
- Effect 中注册 Tauri listener 时保存并调用 unlisten；
- StrictMode 开发重跑不得重复启动长任务、重复注册全局 listener 或重复写入原生状态；
- window label、capability 和 permission 与实际组件调用范围对应；
- 浏览器 mock 通过后仍需覆盖 Tauri webview 或项目已有桌面集成测试；
- 不在前端 bundle、错误日志或状态文件中暴露 updater、签名或插件凭据。

## 门禁

根据项目脚本和 CI 组合：

1. 格式与 React/Hook lint；
2. TypeScript 类型检查；
3. 受影响 Hook、组件和状态测试；
4. 完整前端测试；
5. 生产构建及适用的 SSR/hydration 检查；
6. 浏览器 E2E、可访问性和 Tauri webview/桌面验证。

Builder 运行受影响组件的任务级检查。Verifier 在 rebase 后运行项目定义的完整前端门禁，
并按 `frontend-web` 与 `tauri` 包处理服务、浏览器、应用进程和产物。

## 常见风险

- 缺失 Effect 清理或依赖导致泄漏、旧值和竞态；
- StrictMode 只在开发环境暴露重复副作用；
- key 不稳定导致组件状态落到错误条目；
- mock 测试通过但真实网络、Router、Context 或 Tauri IPC 失败；
- 浏览器 CSR 通过但生产构建、SSR 或 hydration 失败；
- 为“性能优化”滥用 memo、callback 或缓存，增加复杂度却没有测量证据。

报告中注明 React 主版本、renderer、构建框架、状态/路由方案、测试工具、StrictMode、
SSR/hydration 和 Tauri 组合情况。
