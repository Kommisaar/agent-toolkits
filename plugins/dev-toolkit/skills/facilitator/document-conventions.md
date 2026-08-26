# 文档与建模约定

## 交付目标

交付物是面向开发者的非正式 Markdown 文档：

- 可在 Typora 等支持 Mermaid 的编辑器中直接阅读；
- 可由 Git 进行差异审查和版本管理；
- 文字能够独立说明关键结论；
- 图表用于降低理解成本，不替代需求和设计规则；
- 文档结构允许从单文件逐步拆分，不预先制造空壳。

## 默认目录

按需创建以下结构：

```text
docs/design/
├── README.md
├── open-questions.md
├── 00-overview/
│   ├── README.md
│   ├── scope.md
│   ├── system-context.md
│   └── glossary.md
├── 01-requirements/
│   ├── README.md
│   ├── functional.md
│   ├── non-functional.md
│   ├── business-rules.md
│   └── constraints.md
├── 02-use-cases/
│   ├── README.md
│   ├── actors.md
│   ├── catalog.md
│   └── cases/
├── 03-domain-model/
│   ├── README.md
│   ├── domain-model.md
│   ├── business-processes.md
│   └── state-models.md
├── 04-architecture/
│   ├── README.md
│   ├── components.md
│   ├── interfaces.md
│   ├── deployment.md
│   └── decisions/
├── 05-detailed-design/
│   ├── README.md
│   ├── modules/
│   ├── interactions/
│   ├── data-model.md
│   └── api-contracts.md
└── 06-verification/
    ├── README.md
    ├── traceability.md
    ├── consistency-check.md
    └── risks.md
```

## 渐进式拆分

- 初始化时只创建根 `README.md`、`open-questions.md` 和当前阶段需要的文件。
- 每个已创建的阶段目录必须包含 `README.md`，作为阶段摘要和子文档索引。
- 一个主题仍能被顺畅审查时保持单文件；出现多个可独立评审主题或文件明显难以导航时再拆分。
- 用例多时按 `02-use-cases/cases/uc-001-short-name.md` 拆分。
- 架构决策按 `04-architecture/decisions/adr-001-short-name.md` 拆分。
- 详细设计优先按业务模块拆分，而不是按技术类逐文件拆分。
- 不创建空目录占位；需要目录时再创建。
- Mermaid 图默认与解释它的文字放在同一文档，不单独建立图表目录。

## 交付模板

`templates/` 目录按与 `docs/design/` 相同的结构存放每个交付物的模板，模板规定各交付物的标准小节：

- 创建任何交付文档前，先读取 `templates/` 下对应路径的模板；
- 未标注（可选）的小节是必需结构，缺失时需说明理由；标注（可选）的小节按需删除；
- 复制模板后删除模板内的说明文字（`<!-- -->` 注释），替换占位内容；
- 多实例模板（用例、ADR、模块、交互）复制后按占位文件名规则重命名，例如 `uc-xxx-short-name.md` 重命名为 `uc-001-submit-application.md`；
- 模板存在不代表预先创建全部文件，仍按渐进式拆分原则按需创建。

## 根索引

`docs/design/README.md` 使用 [templates/README.md](templates/README.md)，至少包含当前状态、阶段状态、文档导航、关键决策、阻塞问题和最近工作摘要。

只链接已经存在的文件。

## 文档头部

阶段文档建议使用：

```markdown
# 文档标题

> 状态：草稿
> 关联：FR-001、UC-001

## 目的

说明本文解决的问题以及不负责的内容。
```

文档状态使用：

- **草稿**：正在形成内容。
- **待确认**：内容已完整，等待用户确认。
- **已确认**：属于当前设计基线。
- **需修订**：上游变化可能使内容失效。

## 稳定编号

编号一经引用不得因排序变化而重排：

- `FR-001`：功能需求。
- `NFR-001`：非功能需求。
- `BR-001`：业务规则。
- `CON-001`：约束。
- `ACT-001`：参与者。
- `UC-001`：用例。
- `DOM-001`：重要领域概念或规则。
- `CMP-001`：架构组件。
- `INT-001`：接口。
- `SEQ-001`：关键交互。
- `ADR-001`：架构决策。
- `RISK-001`：风险。
- `OQ-001`：开放问题。

被取消的编号保留并标记“已废弃”，不得复用。

## 事实状态

对尚未形成基线的内容使用明确标签：

- **已确认**：用户或可靠资料明确给出。
- **假设**：为推进设计而暂时采用，可被推翻。
- **待确认**：需要用户决策或补充证据。
- **不在范围**：已明确排除。

不要把“常见做法”直接写成项目事实。

## 开放问题

`docs/design/open-questions.md` 使用 [templates/open-questions.md](templates/open-questions.md)。

问题解决后保留条目，填写结论和受影响文档，并将状态改为“已解决”。

## 相对链接

- 项目内文档一律使用相对链接。
- 从根索引链接阶段：`00-overview/README.md`。
- 从阶段文档链接根问题清单：`../open-questions.md`。
- 链接到具体条目时优先同时写稳定编号和文件路径。
- 文件改名后同步修订所有入口和追踪链接。

## Mermaid 选型

默认使用兼容性较高的 Mermaid 类型：

- 系统上下文、业务流程、简化用例、模块关系：`flowchart`。
- 对象或服务交互：`sequenceDiagram`。
- 领域与设计类：`classDiagram`。
- 生命周期：`stateDiagram-v2`。
- 关系型数据结构：`erDiagram`。

`requirementDiagram`、C4 和 `architecture-beta` 只有在目标渲染器确认支持时使用；否则退回文字、`flowchart` 或稳定图表类型。

## Mermaid 编写规则

- Mermaid fenced code block中只写 Mermaid 语法，不混入 `@startuml`、`!include` 或其他 PlantUML 指令。
- 图表标识符使用简短 ASCII 字符，中文放在显示标签中。
- 每张图只回答一个主要问题。
- 图前说明阅读目的，图后说明关键结论和例外。
- 图过大时按业务场景、边界或层次拆分，不通过缩小字体掩盖复杂度。
- 不依赖颜色表达唯一语义；同时使用名称、边界或线型。
- 不为美化强行指定大量坐标或样式。
- 修改图表后同步检查附近文字和关联编号。

## 简化 UML 语义

本 Skill 使用“UML-lite”表达：

- 用例图允许通过 flowchart 近似表达参与者、系统边界和用例关系。
- 活动图允许通过 flowchart 表达流程与分支，不宣称具备完整 UML 令牌语义。
- 组件和部署视图允许使用 flowchart 或经验证可用的 C4。
- 类图、时序图和状态图使用 Mermaid 原生语法。

如果用户要求严格 UML 符号、模型仓库、XMI 或形式化校验，应明确说明 Mermaid 不适合，并建议使用专业建模工具。
