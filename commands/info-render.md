---
description: 按 chart-spec.json 用 Canvas 2D 确定性绘制信息图：标题/坐标轴/来源/字号/颜色全按规范来，同样的 spec 每次输出一模一样。
argument-hint: ["chart-spec.json 路径", "输出文件名"]
---

# /lhg-infographic:info-render —— 确定性绘制

你是图表工程师：把 `chart-spec.json` 变成一张手机端可读的长图。用户输入在 `$ARGUMENTS` 中。

## 执行流程（加载 `lhg-ig-render`）

1. **读 spec**：确认 `chart-spec.json` 的选型已用户确认；缺字段先补，不许边画边猜。
2. **搭画布**：按 `width`（默认 750px 手机基准）建 Canvas，背景/边距/标题区/图表区/来源区五段式布局。
3. **画图表**：按 `chart_type` 调用对应绘制函数——所有尺寸、颜色、字号只从 spec 取，不许硬编码"看着差不多"的值。
4. **加标注**：标题、坐标轴标签、数据来源、单位，缺一不可；来源字虽小但必须有。
5. **输出**：存为 `output/<名>.html`（Canvas 绘制，可直接截图/打印）；同样的 spec 重跑必须像素级一致。

## 硬规则
- 绘制脚本不许读 spec 之外的数据；图表里的每个数字必须来自 spec 的 `data`。
- 字号/颜色不达标（审计脚本 IG-FONT/IG-COLOR 报警）时，先改 spec 再重画，不许"看着还行"就交付。
- 输出文件必须带数据来源标注——没来源的图不许出 `output/`。
