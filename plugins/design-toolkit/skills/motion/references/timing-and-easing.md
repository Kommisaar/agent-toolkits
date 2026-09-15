# 时长与缓动参数表

所有数值来自参考来源核实的参数表；项目已有动效令牌（`--ease-*`、`--duration-*`）时扩展它，不另起平行体系。没有的曲线去 [easing.dev](https://easing.dev/) 或 [easings.co](https://easings.co/) 取现成的，不手搓。

## 频率门控（第一步，先于一切）

| 频率 | 决定 |
| --- | --- |
| 日触 100+ 次：快捷键、命令面板、核心导航 | 不动。键盘触发是否决项，不是判断题 |
| 日触数十次：hover、列表导航、频繁开关 | 近乎不可感知（极快极轻），或不动 |
| 偶尔：模态、抽屉、toast、设置 | 标准动效 |
| 稀有/首次：引导、空状态、成功庆祝 | 惊喜预算（delight 只允许在这一档） |

## 目的词汇（第二步）

反馈 / 空间连续 / 状态指示 / 消除突变 / 解释（仅营销与引导）/ 愉悦（仅稀有档）。命名不出目的就不做；用户正在读或操作的数据不为样式而动。

## 工具阶梯（第三步，自上而下取第一个够用的）

| 需求 | 工具 |
| --- | --- |
| hover、按压、颜色、类/属性切换 | CSS transition |
| 挂载入场、无 JS 状态 | CSS `@starting-style` |
| 预定路径、页面加载期间须保持流畅 | CSS animation（主线程外运行） |
| 程序化控制 + CSS 性能、无库 | WAAPI `element.animate()` |
| 弹簧、布局动画、退场动画、手势驱动 | Motion（motion.dev） |

## 属性规则（第四步）

- 只动 `transform` 与 `opacity`：跳过 layout 与 paint，走合成器。`width`/`height`/`margin`/`padding`/`top`/`left` 触发全部三个阶段。`clip-path` 是特批的第三选择；`height` 仅在手风琴（无 transform 等价物）容忍。
- 禁止 `scale(0)`：从 `scale(0.9–0.97)` + `opacity: 0` 起。
- 弹层（popover/dropdown/菜单/tooltip）`transform-origin` 在触发点（如 Base UI 的 `var(--transform-origin)`）；模态豁免，保持居中。
- `translate()` 百分比相对元素自身尺寸，优于硬编码像素。
- Motion 库写完整 transform 字符串，`x`/`y`/`scale` 短写法不走硬件加速、加载时掉帧；不要用父级 CSS 变量驱动子级 transform。

## 缓动（第五步）

| 场景 | 缓动 |
| --- | --- |
| 入场 / 出场 | `ease-out` |
| 屏内移动 / 形变 | `ease-in-out` |
| hover / 颜色变化 | `ease` |
| 匀速运动仅限进度类（marquee、进度条） | `linear` |
| 默认 | `ease-out` |

UI 禁用 `ease-in`：它把用户最注视的起始瞬间变慢，200ms 的 ease-out 手感快于 200ms 的 ease-in。叙事型营销页的离场可用 ease-in 蓄力（12-principles 目录持此观点），UI 一律 ease-out。

内置缓动太弱，用曲线令牌：

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);      /* 强 ease-out，UI 主力 */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* 强 ease-in-out，屏内移动 */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);   /* iOS 风抽屉曲线 */
```

## 时长（第五步续）

| 元素 | 时长 |
| --- | --- |
| 按钮按压反馈 | 100–160ms |
| tooltip、小弹层 | 125–200ms |
| 下拉、select | 150–250ms |
| 模态、抽屉 | 200–500ms |
| 营销/解释性 | 可更长 |

红线：UI 动画 <300ms（180ms 的下拉比 400ms 的更「跟手」）；同类元素时长必须一致（一个 200ms 一个 150ms 是缺陷）；右键菜单类只做出场动画、不做入场。

## 弹簧（第五步备选）

拖拽带动量、需要打断反转的手势、要「活着」的元素用弹簧，不用定长曲线。Apple 式心智模型（弃用 mass/stiffness/damping 三件套）：

- **damping（阻尼比）**：1.0 = 临界阻尼、无过冲、平滑落位；<1.0 过冲震荡，越低越弹。
- **response（响应）**：到达目标的快慢（秒）。弹簧没有固定时长，稳定时间由参数涌现。

默认阻尼 1.0 起步；bounce（0.1–0.3）只给本身带动的手势（甩动、拖拽释放），淡入的菜单过冲是错的，甩出去的卡片过冲是对的。2D 运动分解为 X/Y 两个独立弹簧（单一距离弹簧在两轴速度不同时失同步）；手势反转时延续速度，不硬切（速度突变是「砖墙」感）。Motion 的 `bounce` + `duration` 参数即此映射。

## 中断与出场（第六步）

- 快速反复触发（toast、开关）用 transition 不用 keyframes：transition 从当前值重定目标，keyframes 从零重启。
- 手势用弹簧：弹簧天然携带速度、可打断。
- 从哪来回哪去：底部进的 toast 从底部出，对称路径让滑动消除可预期。
- 不对称时序用在用户决策处：刻意阶段慢（按住确认 2s linear），系统响应快（松手 200ms ease-out）。

## 编排（第七步）

- 一次只有一个焦点元素在显著运动（staging）；模态入场同时压暗背景聚焦。
- 成组入场 stagger 30–80ms/项（12-principles 目录收紧到 ≤50ms/项）；全部同时入场是「Never Ship」。
- 可交互元素保留按压态（active 时轻微 scale）；squash/stretch 形变控制在 0.95–1.05；需要过冲回落的效果用弹簧，不用缓动模拟。
