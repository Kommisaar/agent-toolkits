---
name: init
description: 手动运行的一次性项目初始化工具。把固定的设计协作开发准则以受管段落安装到项目 AGENTS.md，使编码 Agent 在日常开发中遵循查设计再改码、设计编号追踪、偏差留痕和新需求先修订设计等纪律。当用户明确要求初始化或更新设计准则、把设计规范写入 AGENTS.md 时使用；每个项目通常只运行一次，可安全重跑。
disable-model-invocation: true
---

# Dev Toolkit Init

## 目标

把固定的设计协作准则安装到项目根 `AGENTS.md`，供编码 Agent 长期遵循。本 Skill 只安装或更新受管段落，不参与设计、访谈、文档审查或准则生成。

## 前置条件

- 只接受用户显式调用，不在普通开发任务中自动触发。
- 项目必须存在 `docs/design/README.md`；不存在时停止，不写入文件，并建议先运行 `facilitator` 建立设计文档。
- 用户显式调用即视为对本次 `AGENTS.md` 受管段落写入的授权，不再二次请求确认。
- [agent-guidelines.md](agent-guidelines.md) 中两条 marker 包围的内容是唯一准则来源，不根据阶段状态或编号动态裁剪。

## 执行步骤

1. 确认项目根 `docs/design/README.md` 存在，否则停止。
2. 读取 [agent-guidelines.md](agent-guidelines.md)，提取从以下起始 marker 到结束 marker 的完整区块，包含 marker 本身；忽略区块外的维护说明：
   - `<!-- design-guidelines:start -->`
   - `<!-- design-guidelines:end -->`
3. 读取项目根 `AGENTS.md`；文件不存在时按“无 marker”处理。
4. 统计 `AGENTS.md` 中两种 marker，并按以下规则分类：
   - **无 marker**：两种 marker 均未出现；
   - **有效受管块**：两种 marker 各出现一次，均独占一行，且起始 marker 位于结束 marker 之前；
   - **异常 marker**：仅出现一端、任一 marker 重复、顺序颠倒、嵌套或 marker 未独占一行。
5. 遇到异常 marker 时立即停止，不修改 `AGENTS.md`，报告具体异常位置并要求用户先修复。
6. 写入：
   - `AGENTS.md` 不存在：创建文件，内容为完整受管块；
   - 文件存在且无 marker：保留原内容，在文件末尾以一个空行分隔后追加完整受管块；
   - 存在有效受管块：从起始 marker 到结束 marker（含两端）整体替换为模板受管块，受管块外内容保持不变。
7. 报告执行的是“创建”“追加”或“更新”、目标文件路径以及是否可以安全重跑。

## 约束

- 只管理两条 marker 及其之间的内容，`AGENTS.md` 中其他内容不得改写、重排或格式化。
- 不把 [agent-guidelines.md](agent-guidelines.md) 中受管块外的维护注释写入项目。
- 不解析阶段状态，不推断启用编号，不生成项目专属措辞。
- 正常 marker 状态下直接写入，不展示预览或请求二次确认。
- 不创建、不修改 `docs/design/` 下的任何文档。
