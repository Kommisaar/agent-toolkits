---
id: python
label: Python
applies-to: 仓库含 pyproject.toml、setup.py、requirements*.txt 或以 *.py 源码为主
---

## Python 专项规范

### 模块与依赖边界

- 一个类或一族紧密相关的函数一个模块；模块按层分包（models、services、api 等）。
- `__init__.py` 只做显式导出，不写逻辑。

### 类型、数据与接口契约

- PEP 8；公共 API 必写类型注解，内部代码尽量补全。
- 文件路径用 pathlib，禁止手工拼接字符串路径。
- 公共 API 的 docstring 写语义、边界条件与失败行为，不复述类型注解已有的信息。

### 状态、并发与资源生命周期

- 文件、连接、锁等资源用 with 或显式 close 管理，禁止依赖 GC 兜底。
- asyncio 任务必须被等待或显式取消；禁止创建后无人引用的 fire-and-forget 任务。
- 共享可变状态限于明确标注的模块；跨模块共享须经调用方显式传入。

### 错误、安全与可观测性

- 定义领域异常层级，禁止裸 except 与 `except Exception: pass`。
- logging 用模块级 logger；错误日志带 exc_info 与上下文字段。
- 用返回值表达失败时必须显式标注（Optional 并写明语义），禁止隐式 None 装成功。

### 测试与可判定验收

- pytest 全过；ruff、mypy 干净，项目已配置其他等价工具时以其为准。

### 反模式与替代方案

- 禁止 try 包住整个函数的粗粒度防御，只包会抛的具体语句。
- 禁止 `*args, **kwargs` 透传不确定签名，改为显式参数列表。
- 禁止用缓存或默认参数掩盖设计问题，改用显式依赖传入。
