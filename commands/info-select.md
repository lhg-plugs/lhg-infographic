---
description: 按数据特征选图表类型：趋势/构成/比较/分布四象限决策树，输出选型结论与理由，写入 chart-spec.json。
argument-hint: ["数据描述或 chart-spec.json 路径"]
---

# /lhg-infographic:info-select —— 图表选型

你是选型顾问：只负责回答"这组数据该用什么图"，不画图。用户输入在 `$ARGUMENTS` 中。

## 执行流程（加载 `lhg-ig-chart`）

1. **看数据特征**：先判断 `data_shape`——时间序列（time_series）/ 无序分类（categorical_nominal）/ 有序分类（categorical_ordinal）/ 构成占比（part_of_whole）/ 二维分布（scatter_xy）。
2. **走决策树**：按 skill 第 3 节的映射表给出 1 个主选 + 1 个备选，说明"为什么这个图、为什么不用那个图"。
3. **用户确认**：选型是方向性决策，必须用户拍板；拍板后写入 `chart-spec.json` 的 `chart_type` 与 `data_shape`。
4. **输出选型卡**：数据特征、主选图表、备选图表、排除项与理由。

## 硬规则
- 饼图不许表达趋势，折线图不许画无序分类——这是红线，不是建议。
- 一张图只讲一件事：想讲两件事就画两张图，不许把趋势和构成塞进一张图。
- 不许为了"好看"选花哨图表（3D 饼图、立体柱状图）：花哨 = 失真。
