---
id: tauri
label: Tauri 2
applies-to: Tauri 2 桌面与移动应用、Rust 后端、Web 前端和跨平台打包
---

# Tauri 2

## 组合方式

Tauri 是框架叠加包，不替代基础语言包：

- 始终组合 `rust`；
- 使用 JavaScript/TypeScript 前端时组合 `typescript`；
- 存在浏览器 UI、组件或 E2E 时组合 `frontend-web`；
- 使用 React 时再组合 `react`；
- 前端使用其他工具链时继续遵守对应项目约定。

## 识别

出现以下证据时应用本包：

- `src-tauri/Cargo.toml` 中依赖 Tauri；
- `src-tauri/tauri.conf.json`、JSON5 或 TOML 形式的 Tauri 配置；
- `src-tauri/capabilities/`、`src-tauri/permissions/`；
- `@tauri-apps/api`、`@tauri-apps/cli` 或 Tauri CLI 脚本；
- Tauri 插件、commands、events、channels、sidecars 或移动端生成目录。

仅存在普通 Rust 与 Web 前端目录时不要误判为 Tauri。

从 `src-tauri/Cargo.toml`、锁文件和前端 CLI 依赖确认主版本。本包只描述 Tauri 2；检测
到 Tauri 1 时标记为版本不匹配，不套用 Tauri 2 的 capability/permission 规则。

## 配置与构建边界

先读取实际 Tauri 配置和项目脚本，重点解析：

- `build.beforeDevCommand`、`beforeBuildCommand`；
- `build.devUrl`、`frontendDist`；
- app、window、webview、bundle 和 plugin 配置；
- 当前启用的桌面、Android、iOS target；
- CI 中的平台矩阵、系统依赖和签名步骤。

使用项目声明的 npm/pnpm/Yarn/Bun/Cargo 命令。不要同时重复执行配置中已经由 Tauri CLI
触发的前端构建，除非门禁明确要求独立验证。

`tauri dev` 是长期开发进程，不作为可退出门禁。需要启动时记录 PID、dev server 和端口，
等待明确健康信号，并在完成后只停止本轮创建的进程。

## 权限与安全

Tauri 2 的 capabilities 和 permissions 属于安全边界，任何变化都至少按中风险处理：

- 检查 capability 绑定的 window、webview、platform 和 permission；
- 遵守最小权限，不用宽泛 allow 规则掩盖调用失败；
- 插件权限必须与实际前端 API 调用对应；
- `src-tauri/gen/schemas/` 等生成 schema 不手工修改；
- 远程 URL、CSP、文件系统、Shell、HTTP、窗口和 updater 权限需要额外审查；
- updater 公钥可以进入配置，私钥、签名密码和发布凭据不得读取或写入状态；
- 新增 plugin、sidecar、外部二进制或远程 endpoint 必须请求确认。

capability 文件在项目中的启用方式以当前配置为准，不能仅根据文件存在断言其生效范围。

## IPC 契约

同时审查 Rust 与前端两侧：

- `#[tauri::command]` 名称、参数、返回值和错误序列化；
- `invoke` 调用名称、字段命名、可选性和 TypeScript 类型；
- events、channels 和 listeners 的生命周期及清理；
- async command 中的阻塞工作、线程边界和状态锁；
- managed state、窗口标签和权限检查；
- 前后端默认值、枚举、路径、时间和二进制数据编码。

只修改单侧但未验证契约时不得批准。mock 必须与实际 Tauri API 和错误行为保持一致。

## 门禁发现

根据仓库文档和 CI 组合以下门禁，不机械套用不存在的命令：

1. 前端格式、lint、类型检查和单元测试；
2. `src-tauri` Rust 格式、check、clippy 和测试；
3. 前端生产构建；
4. Tauri debug 构建或项目配置的无 bundle 构建；
5. 项目已有的 WebDriver、桌面集成或端到端测试；
6. 需要交付验证时的平台 bundle/package 构建。

Builder 运行受影响侧的任务级检查。Verifier 在 rebase 后独占 worktree，执行任务包指定的
完整前端、Rust 和 Tauri 门禁。完整 `tauri build` 可能耗时且依赖平台工具链，应由项目
CI 或运行卡明确要求，不能因为当前主机无法覆盖其他平台就宣称跨平台通过。

## 桌面与移动验证

- Web UI 在普通浏览器通过不等于 Tauri webview 中通过。
- WebDriver 测试只在项目已经配置驱动、应用构建和进程清理时执行。
- 记录宿主 OS、架构、Rust target、webview/runtime 和实际验证平台。
- Windows、Linux、macOS 的系统库与打包结果不可互相替代。
- Android/iOS 需要对应 SDK、IDE、模拟器或设备；缺失时标记 `UNVERIFIED`，不自动安装
  系统级依赖。
- 移动端 `dev --open` 会打开平台 IDE，不用于无人值守门禁，除非用户明确授权。

## Sidecar 与打包

- 核对 sidecar 文件名、target triple、可执行权限和目标平台覆盖；
- 不执行来源不明的外部二进制；
- 检查图标、资源、identifier、版本号和 bundle target；
- 签名、公证、发布和 updater artifact 属于外部副作用，不自动执行；
- release pipeline 中的 Token、证书和私钥不能写入日志或 `auto-iter/runs`。

## 生成物与污染

重点检查：

- 前端 `dist` 与框架缓存；
- `src-tauri/target` 或自定义 `CARGO_TARGET_DIR`；
- `src-tauri/gen/schemas` 和移动端生成项目；
- bundle、installer、DMG、AppImage、MSI、NSIS、APK、AAB、IPA 等产物；
- capability/permission 文件、锁文件、图标和 sidecar；
- WebDriver 截图、日志、应用二进制和测试报告。

只有任务包明确允许且项目已忽略的构建产物可以保留。权限、锁文件、配置和已跟踪生成物
变化必须作为真实 diff 审查，Verifier 不得自动更新或还原。

## 常见风险

- 前端与 command 参数或错误类型漂移；
- 权限过宽，或 capability 没绑定到实际窗口；
- 开发模式正常但 `frontendDist`、生产构建或 bundle 失败；
- async command 阻塞 UI、锁跨 await 或事件 listener 泄漏；
- 本地主机通过但其他 target、sidecar 或系统依赖缺失；
- updater、签名和发布步骤在验证阶段产生外部副作用。

报告中注明组合的基础 stack、Tauri 主版本、CLI 调用方式、宿主平台、验证 target、
capability/permission 变化、bundle 范围和未覆盖平台。
