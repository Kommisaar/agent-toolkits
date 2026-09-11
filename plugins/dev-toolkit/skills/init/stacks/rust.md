---
id: rust
label: Rust
applies-to: 仓库含 Cargo.toml 或 rust-toolchain 文件
---

## Rust 专项规范

### 模块与依赖边界

- 一个类型或组件一个模块文件；模块目录与 mod 声明一致，不把多个无关类型塞进一个文件。
- bin 与 lib 分离；纯逻辑与 IO 分层，IO 边界集中在最外层模块。
- 错误类型一个概念一个文件，与领域模型同层放置。

### 类型、数据与接口契约

- rustfmt 默认配置，不局部改写；没有调用方的项不 pub，保持私有。
- `unsafe` 块必须写 `// SAFETY:` 注释说明成立前提；公开 unsafe API 写 `# Safety` 文档段。

### 状态、并发与资源生命周期

- 跨线程共享按最小范围选型 Arc/Mutex/RwLock；锁内禁止跨 await 点。
- Drop 只做资源释放，不做可能失败的外部交互；外部交互放显式 close/shutdown 方法。
- spawn 的任务有明确取消路径；JoinHandle 必须被等待、传播错误或注释写明放弃理由。

### 错误、安全与可观测性

- 库代码定义领域错误类型（项目未选型时用 thiserror）；应用层才允许 anyhow。
- 禁止 `let _ =` 与 `.ok()` 吞错；确需忽略必须注释写明理由。
- 日志遵循项目统一 logger，未配置时用 tracing；错误必须携带上下文（操作、来源、原因）。

### 测试与可判定验收

- `cargo fmt --check`、`cargo clippy -- -D warnings`、`cargo test` 全过；项目声明的警告策略优先。

### 反模式与替代方案

- 禁止为“泛型灵活性”提前抽象，先写具体实现，出现第二个用例再泛化。
- 非测试、非启动不变量代码禁止 unwrap/expect，改用 `?` 或显式错误分支。
- Option 已表达的可空不再叠加默认值装成功；缺失就是错误路径。
