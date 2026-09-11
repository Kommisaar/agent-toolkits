---
id: rust
label: Rust
applies-to: Cargo workspace、Rust 应用、库、CLI 和服务
---

# Rust

## 识别

出现 `Cargo.toml`、`Cargo.lock`、`rust-toolchain.toml`、`.cargo/config.toml` 或 `.rs`
源码时应用本包。先判断单 crate、Cargo workspace 和 feature 组合。

## 工具链

1. 使用 `rust-toolchain.toml`、CI 或项目文档声明的 toolchain。
2. 尊重 `.cargo/config*`、target、runner、linker 和交叉编译配置。
3. 不自动执行 toolchain 更新、依赖升级或 `cargo update`。
4. 是否提交 `Cargo.lock` 以仓库现状和项目约定为准。
5. 需要私有 registry、系统库、数据库或外部服务时在任务包中显式授权。

## 门禁发现

根据仓库约定组合：

- 格式：`cargo fmt --check`；
- 快速检查：`cargo check`；
- lint：`cargo clippy` 及项目声明的 target、feature 和警告策略；
- 测试：`cargo test`、workspace、all-targets 或指定 feature；
- 构建：项目要求的 debug、release、目标平台或示例；
- 文档：doctest、rustdoc 或项目脚本；
- 额外工具：nextest、deny、audit、miri、bench，仅在项目已有配置时执行。

不要机械添加 `--all-features` 或 `-D warnings`；这些参数必须来自项目文档、CI 或任务包，
否则可能验证不存在于实际交付矩阵中的组合。

## 并发与缓存

- 多个 Builder/Verifier 并发时，每个 worktree 使用独立 `CARGO_TARGET_DIR`，避免构建
  指纹和生成物互相污染。
- 单任务可按项目约定使用已有缓存，但不能让两个写任务共享同一 target 目录。
- Verifier 报告实际 target 目录；只清理自己创建且所有权明确的目录。
- Cargo registry/git 下载缓存可共享，但不能由本任务删除或重写。

## 执行策略

- Builder 先运行受影响 crate 的测试和检查。
- Verifier 在 rebase 后按 workspace 契约运行完整 fmt、clippy、test 和 build。
- feature、target、平台和环境变量必须记录，默认 feature 通过不能代表其他组合通过。
- 测试超时、死锁或不退出时按超时失败处理，不无限等待。
- unsafe、FFI、并发和持久化相关改动需要更严格的审查和针对性测试。

## 生成物与污染

重点检查 `Cargo.lock`、target、bindgen/protobuf/schema 生成代码、快照、测试夹具和基准
结果。Verifier 不得用 `cargo fix`、自动格式化写入或快照接受命令修改待验提交。

## 常见风险

- feature 组合遗漏或平台条件编译失败；
- async runtime 嵌套、阻塞调用和取消安全；
- 生命周期正确但资源释放、panic 或错误上下文不完整；
- unsafe 不变量、FFI 所有权和 ABI 漂移；
- 序列化兼容、整数溢出和路径编码；
- 测试共享端口、临时目录或全局环境导致并发不稳定。

报告中注明 toolchain、workspace 范围、features、targets、`CARGO_TARGET_DIR` 和所有跳过项。
