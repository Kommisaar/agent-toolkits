---
id: java
label: Java 与 JVM
applies-to: 仓库含 pom.xml、build.gradle 或 build.gradle.kts，或 src/main/java、src/main/kotlin 目录
---

## Java 与 JVM 专项规范

### 模块与依赖边界

- Kotlin 顶级函数按单一职责归入对应文件。
- package 与目录路径严格一致；controller / service / repository 分层，禁止跨层直接引用。
- 接口定义与实现分文件；不建“万能接口”。

### 类型、数据与接口契约

- 遵循各语言官方约定：Java 类 PascalCase、常量 UPPER_SNAKE；Kotlin 优先 val、表达式体与数据类。
- 公共 API 的 Javadoc/KDoc 写空值语义、抛出条件、线程安全与调用契约，不复述签名。

### 状态、并发与资源生命周期

- 资源用 try-with-resources / use 关闭，禁止依赖 finalize 兜底。
- 禁止吞 InterruptedException，必须恢复中断标志或上抛。
- 共享可变状态标注可见性与同步策略；优先不可变对象与并发容器。

### 错误、安全与可观测性

- 业务错误定义领域异常类型；禁止 `catch (Exception e)` 一网打尽。
- catch 后必须记日志或转译上抛（保留 cause），禁止吞掉。
- 日志用 SLF4J 参数化占位（项目已配置其他门面时以其为准），携带操作与关键参数。
- 禁止返回 null 表示失败；用 Optional、Result 或密封类型表达。

### 测试与可判定验收

- 行为变化配套 JUnit 测试；构建与测试命令可判定、可复跑。

### 反模式与替代方案

- 禁止 Utils 万能类堆积；职责说不清的类不建。
- 禁止用委托或注解生成掩盖分层越界。
