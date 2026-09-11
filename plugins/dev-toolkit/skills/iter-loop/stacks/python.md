---
id: python
label: Python
applies-to: Python 应用、库、服务、脚本和数据处理项目
---

# Python

## 识别

出现 `pyproject.toml`、`setup.py`、`setup.cfg`、`requirements*.txt`、`Pipfile`、
`poetry.lock`、`uv.lock`、`tox.ini` 或 Python 包目录时应用本包。

## 环境与依赖

1. 优先读取仓库文档、`pyproject.toml`、CI 和锁文件。
2. 使用项目已经选择的 uv、Poetry、Pipenv、pip、tox、nox 或其他工具，不混用环境管理器。
3. 遵守项目声明的 Python 版本、实现和平台矩阵。
4. worktree 使用项目约定的独立虚拟环境；不把其他 worktree 的可写虚拟环境直接复用。
5. 缺少依赖时只有任务包明确授权才能安装，不生成或升级锁文件。

多个依赖来源相互冲突、解释器版本不可用或必须访问私有源时返回 `BLOCKED`。

## 门禁发现

从项目配置、CI、tox/nox session 和脚本中识别：

- 格式检查：Black、Ruff format 或项目工具；
- lint：Ruff、Flake8、Pylint 等；
- 类型检查：mypy、Pyright、Pyre 等；
- 单元/集成测试：pytest、unittest、tox/nox；
- 打包验证：build、twine check 或项目脚本；
- 文档、迁移和生成物检查。

不同时运行互相替代的工具组合，除非仓库本身要求。不要根据工具常见用法覆盖项目参数。

## 执行策略

- Builder 先运行受影响模块和测试文件，再执行相关 lint/类型检查。
- Verifier 在 rebase 后运行仓库定义的完整环境或受支持版本矩阵。
- pytest 使用一次性模式，不启用长期 watch；并行参数以项目配置为准。
- 集成测试需要数据库、消息队列或网络服务时，必须使用任务包给出的隔离环境。
- 测试依赖时间、随机数、locale 或环境变量时，记录固定方式和实际值。

## 生成物与污染

重点检查：

- `__pycache__`、`.pytest_cache`、`.mypy_cache`、`.ruff_cache`；
- coverage、JUnit、HTML 报告；
- `build`、`dist`、`*.egg-info`；
- 自动生成客户端、模型、迁移和快照；
- notebook 输出和数据文件。

缓存只有在项目忽略且任务包允许时才视为预期。迁移、锁文件、notebook 输出和已跟踪生成物
变化必须由 Builder 明确实现并审查，Verifier 不得生成后直接接受。

## 常见风险

- 同步与异步调用混用造成资源泄漏；
- 可变默认参数、时区和 Decimal/float 差异；
- 类型检查通过但运行时输入未校验；
- 测试只在开发者 Python 版本通过；
- fixture、monkeypatch 或 mock 泄漏状态；
- 数据库事务、迁移顺序和回滚路径未覆盖。

报告中注明解释器版本、环境工具、执行的 session、跳过项、外部服务和基线失败。
