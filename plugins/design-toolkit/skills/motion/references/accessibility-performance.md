# 可访问性与性能

降级与性能不是动效的附件，是它能否发布的先决条件。

## 性能：只走合成器

浏览器渲染管线是 layout → paint → composite。动 `transform` 与 `opacity` 只走合成器（常在 GPU），60/120fps 下依然流畅；动 `width`/`height`/`top`/`left`/`margin`/`padding`/`box-shadow`/`filter` 每帧触发 layout 或 paint，阻塞主线程。

昂贵动画换便宜等价物：

| 昂贵 | 便宜等价 |
| --- | --- |
| `left`/`width` 位移或变宽 | `transform: translateX()/scaleX()`（配 `transform-origin`） |
| `box-shadow` 过渡（每帧重绘模糊区） | 阴影画一次在 `::after` 上，只过渡其 `opacity` |
| `height: auto` 展开 | grid 行轨道 `0fr → 1fr` 过渡（跨浏览器默认）；支持处用 `interpolate-size: allow-keywords` / `calc-size()` |
| 布局重排动画（重排序、跨容器移动） | FLIP：记录 First/Last 位置，施加反向 transform 再动画归位，DOM 落在真实终态 |

避免 layout thrashing：`getBoundingClientRect`/`offsetWidth` 这类读取跟在写入后会强制同步重排；循环里读写交替等于每帧几十次强制重排。批量读 → 一次写 → WAAPI/Motion 播放 transform。

## reduced-motion：分级降级，不是开关

`prefers-reduced-motion: reduce` 表示前庭风险动作（位移、视差、无限循环）引起眩晕，正确响应是**移除危险动作、保留定向线索**（WCAG 2.3.3 / C39）：

- **Tier 1 移除**：视差、大幅位移、无限循环（marquee/spin）、缩放镜头。
- **Tier 2 降为淡入淡出**：去 transform，保留 `opacity`/`color` 过渡。
- **Tier 3 保留**：帮助理解状态变化的轻微过渡。

```css
/* 复杂效果用正向查询：默认静止可见，允许时才动 */
.hero { opacity: 1; }
@media (prefers-reduced-motion: no-preference) {
  .hero { animation: zoom-in 1.2s ease both; }
}

/* 逐元素分级，优于全局核爆 */
@media (prefers-reduced-motion: reduce) {
  .card { transition: opacity 150ms ease, background-color 150ms ease; } /* 去 transform 留 opacity/color */
  .parallax-layer { transform: none !important; }  /* 危险动作直接移除 */
}
```

JS 侧用 `matchMedia('(prefers-reduced-motion: reduce)')` 门控；Motion 用 `useReducedMotion()` 决定目标值（如关闭抽屉的 `-100%` 在降级时取 `0` 直接切换）。全局 `animation-duration: 0.01ms !important` 兜底只作最后手段——它连帮助理解的过渡一起杀掉。

## hover 门控

触摸设备 tap 会先触发假 hover，hover 动效必须门控：

```css
@media (hover: hover) and (pointer: fine) {
  .element:hover { transform: scale(1.05); }
}
```

## 手感检查（代码判断不了的部分）

交叉淡入的分寸、弹簧的过冲、入场列表的透明度/高度平衡——这些从代码里读不出来。检查方法：以 2–5 倍时长慢放；DevTools 动画检查器逐帧步进；手势效果上真机；隔天用新鲜眼睛再看一遍。写进改进计划的验证段，不要猜值。
