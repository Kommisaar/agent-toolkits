# 阶段 04：架构

## 阶段目标

根据需求、质量属性和约束，确定系统的主要技术责任边界、组件协作、接口方向、数据所有权和部署方式。

架构设计应解释取舍，而不只是画模块框图。技术选择必须能追溯到需求、风险或约束。

## 进入阶段前

确认或读取：

- 系统上下文和约束；
- 功能与非功能需求；
- 关键用例及高风险失败路径；
- 领域边界、业务不变量和状态模型；
- 现有代码、基础设施或组织边界；
- 与技术选型有关的开放问题。

## 架构驱动因素

优先提取：

- 最关键的业务场景；
- 性能、可用性、安全和一致性目标；
- 数据规模、峰值和增长假设；
- 外部系统及其可靠性；
- 必须沿用的技术和运行环境；
- 团队边界、交付节奏和运维能力；
- 最高的不确定性和失败成本。

如果缺少驱动因素，不应直接给出确定架构。

## 访谈顺序

### 责任与边界

- 哪些业务能力需要独立演进、部署或授权？
- 哪些数据必须由一个明确组件拥有？
- 哪些操作必须处于同一一致性边界？
- 团队或外部供应方边界是否影响组件划分？

### 交互与接口

- 关键用例跨越哪些边界？
- 哪些调用必须同步返回，哪些可以异步处理？
- 失败、超时、重试和重复消息如何处理？
- 接口由谁拥有，兼容性需要保持多久？

### 数据与一致性

- 关键数据的权威来源在哪里？
- 是否允许复制、缓存或最终一致？
- 跨组件业务操作如何保持不变量？
- 数据迁移、审计、保留和删除如何处理？

### 运行与部署

- 系统运行在哪些环境和网络区域？
- 哪些单元需要独立扩缩容或故障隔离？
- 有哪些数据库、队列、对象存储或外部服务？
- 发布、回滚、配置和密钥由谁管理？

### 安全与可观测性

- 身份在哪个边界建立并如何传递？
- 授权由哪个组件执行？
- 敏感数据经过哪些信任边界？
- 哪些指标、日志、追踪和告警用于判断关键用例是否健康？

## 组件条目

`components.md` 使用 [templates/04-architecture/components.md](templates/04-architecture/components.md)，包含架构总览图骨架和组件条目结构。

组件名称应体现业务或技术责任，不使用“Common”“Utils”等无法判断边界的名称。

## 架构总览图

默认使用兼容性较高的 flowchart，骨架见模板。

图后说明：

- 每个组件的责任；
- 数据所有权；
- 接口协议和方向；
- 信任边界和故障边界；
- 图中省略的内容。

目标渲染器确认支持时，可以使用 C4 表达 Context、Container、Component 或 Deployment 视图。C4 仍然是 Mermaid 的实验功能；不得把 C4-PlantUML 的 `@startuml`、`!include`、sprite、skinparam 等指令放入 Mermaid。

## 接口清单

`interfaces.md` 使用 [templates/04-architecture/interfaces.md](templates/04-architecture/interfaces.md)，先记录架构级接口；详细字段和消息结构留到详细设计阶段。

## 部署视图

`deployment.md` 使用 [templates/04-architecture/deployment.md](templates/04-architecture/deployment.md)，覆盖运行单元、网络区域与信任边界、数据存储与备份、外部服务、配置与密钥、可用性与故障恢复和监控入口。

部署图仍可使用 flowchart。除非部署复杂度影响设计，不绘制云厂商所有资源。

## 架构决策

重大且难以逆转的选择创建 `decisions/adr-xxx-short-name.md`：复制 [templates/04-architecture/decisions/adr-xxx-short-name.md](templates/04-architecture/decisions/adr-xxx-short-name.md) 后按 `adr-编号-短名.md` 重命名。

不要为普通库选择或容易撤销的局部实现创建 ADR。

## 产物

按需创建：

- `docs/design/04-architecture/README.md`
- `docs/design/04-architecture/components.md`
- `docs/design/04-architecture/interfaces.md`
- `docs/design/04-architecture/deployment.md`
- `docs/design/04-architecture/decisions/adr-xxx-short-name.md`

阶段 `README.md`（模板：[templates/04-architecture/README.md](templates/04-architecture/README.md)）汇总架构驱动因素、总览图、关键组件、主要决策、风险和子文档。

## 阶段完成判断

准备进入门禁前确认：

- 架构边界能够承载关键用例和领域规则；
- 关键数据、接口和故障责任有明确所有者；
- 非功能需求具有对应设计响应；
- 外部依赖、部署和信任边界已识别；
- 重大取舍已记录候选方案与后果；
- 需要详细设计的高风险路径已经确定。

完成后执行架构门禁，再请求用户确认。
