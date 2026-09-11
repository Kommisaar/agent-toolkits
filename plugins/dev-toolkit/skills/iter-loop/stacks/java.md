---
id: java
label: Java 与 JVM
applies-to: Maven、Gradle、Java、Kotlin 和 JVM 多模块项目
---

# Java 与 JVM

## 识别

出现 `pom.xml`、`.mvn/`、`mvnw`、`build.gradle*`、`settings.gradle*`、`gradlew`、
Java/Kotlin 源码或 JVM 工具链配置时应用本包。

## 构建工具与 JDK

1. Maven Wrapper 存在时优先使用 `mvnw`；Gradle Wrapper 存在时优先使用 `gradlew`。
2. 仓库同时包含 Maven 和 Gradle 时，根据根文档、模块归属和 CI 选择，不混合执行。
3. 使用 toolchain、`.java-version`、SDK 配置、构建文件或 CI 声明的 JDK。
4. 不自动升级 Wrapper、插件、BOM 或依赖版本。
5. 私有仓库、签名、凭据和企业镜像缺失时返回 `BLOCKED`，不改用不可信源。

Windows 使用对应 wrapper 脚本；命令语法以当前 shell 和仓库 CI 为准。

## 门禁发现

从 wrapper、构建生命周期、CI 和项目脚本识别：

- 编译和资源处理；
- 单元测试；
- 集成、契约或端到端测试；
- Checkstyle、SpotBugs、PMD、Error Prone、ktlint、detekt 等静态检查；
- 打包、模块边界和依赖规则；
- 数据库迁移、代码生成和文档检查。

Maven 不默认把 `-DskipTests` 视为验证；Gradle 不复用被任务包禁止的跳过参数。只有项目
约定允许时才使用离线模式或跳过耗时阶段。

## 执行策略

- Builder 先运行受影响 module 的编译、静态检查和测试。
- Verifier 在 rebase 后按根构建契约运行完整 reactor 或 multi-project 门禁。
- 多模块过滤只用于快速反馈，合并前必须覆盖受影响依赖方。
- Gradle daemon、并行 worker 和 Maven 并行参数以项目配置及机器预算为准。
- Testcontainers、数据库和消息系统必须使用隔离资源，并记录启动和清理结果。

## 生成物与污染

重点检查：

- Maven `target`、Gradle `build`、`.gradle` 和测试报告；
- 代码生成的源码、OpenAPI/protobuf 客户端和 annotation processor 输出；
- 锁文件、依赖验证元数据和 Wrapper 文件；
- 数据库迁移、快照和 golden files。

构建目录和缓存只有在项目忽略且任务包允许时才视为预期。Verifier 不提交生成源码、不更新
依赖校验、不接受快照，也不删除共享的用户级 Maven/Gradle 缓存。

## 常见风险

- 本地 JDK 与 CI toolchain 不一致；
- 多模块只测当前模块，遗漏下游二进制或源码兼容；
- 测试依赖固定端口、时区、locale、文件编码或执行顺序；
- Spring/Jakarta、序列化和反射配置只在运行时失败；
- Gradle 配置缓存或增量构建掩盖干净构建问题；
- 数据库事务、迁移和容器清理不完整。

报告中注明 JDK、构建工具与 Wrapper 版本、模块范围、测试类型、外部服务和所有跳过项。
