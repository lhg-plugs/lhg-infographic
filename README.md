<!-- About 简介（推送后填写到仓库 About 栏）：
信息图表专家：数据/文章→图表选型→Canvas 确定性绘制→手机端可读性审计，小白也能做出版级信息图 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-infographic
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, infographic, data-visualization, chart, design, ai-agents -->

# lhg-infographic：信息图表专家

> **一句话介绍**：给 AI 助手装上"信息图生产线"——需求澄清、数据整理、图表选型、Canvas 确定性绘制、16 条数据-图表映射与可读性审计，小白也能做出手机端可读的出版级信息图。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-infographic
> /plugin install lhg-infographic@lhg-plugs
> ```

## 它是什么

`lhg-infographic` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`infographic` 信息图一条龙，`info-select` 图表选型，`info-render` 确定性绘制，`info-audit` 可读性审计
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：需求澄清与数据整理、图表选型决策树、Canvas 确定性绘制规范、手机端可读性评审
- **3 个专家 agent**：信息设计师、图表工程师、可读性评审员
- **2 个硬门 hooks**：commit 前审计拦截（有 blocker 不许提交）、spec 写入后数据来源缺失提醒（均可一键豁免）
- **16 条确定性审计规则**：纯 Python、零第三方依赖，秒级出结果

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-infographic:infographic` | 一句话 → 完整信息图（澄清→选型→绘制→自检→审计） | `/lhg-infographic:infographic "Q3销量数据 公众号"` |
| `/lhg-infographic:info-select` | 按数据特征选图表类型（决策树） | `/lhg-infographic:info-select "月度销量趋势"` |
| `/lhg-infographic:info-render` | 按 chart-spec.json 确定性绘制 | `/lhg-infographic:info-render chart-spec.json` |
| `/lhg-infographic:info-audit` | 16 条规则审计 + 手机端人工评审 | `/lhg-infographic:info-audit` |

## 信息图工程约定

插件审计脚本按以下项目结构工作（`/infographic` 会自动建好），核心是 `chart-spec.json`——绘制与审计的唯一输入：

```
infographic-<主题>/
├── chart-spec.json      # 图表规格：标题/类型/数据/字号/颜色/来源
├── data/                # 原始数据文件
└── output/              # 绘制产物（HTML）
```

`chart-spec.json` 关键字段：`title`（一句人话标题）、`chart_type`（line/bar/pie/scatter）、`data_shape`（time_series/part_of_whole/…）、`data`（`[{"label","value"}]`）、`fonts`（title/label/tick 三级字号）、`colors`（background/text/series）、`source`（数据来源三要素）。

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审（人）：

1. 先跑 `scripts/audit/infographic_audit.py`（16 条规则：标题来源 2、映射 5、字号 2、颜色 2、数据 5），零 LLM 成本；
2. 发现分三级：**blocker**（必须修，commit 前 hook 会拦截）、**warning**（修或写豁免理由）、**nit**（顺手修）；
3. 再过人工四项：手机 375px 实看、遮图例看颜色、来源三要素、信息量控制（一张图只讲一件事）。

blocker 清零才算做完；为清零改规则算作弊，不许。映射错误（饼图画趋势/折线画无序分类）是方向性错误：修法是换图表类型，不是调参数。

## 目录结构

```
lhg-infographic/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：infographic / info-select / info-render / info-audit
├── skills/                  # 4 个平台中立 skill（lhg-ig-brief/chart/render/review）
├── agents/                  # 3 个专家 agent（info-designer / chart-engineer / info-reviewer）
├── hooks/                   # 2 个硬门（commit 前审计拦截 / 来源缺失提醒）+ 豁免说明
├── scripts/audit/           # 16 条确定性审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（info-bad 坏 / info-good 好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你有一组数据/一篇文章，想做成朋友圈/公众号能发的信息图时 → 用 `/lhg-infographic:infographic`
- 你不确定这组数据该用柱状图还是折线图时 → 用 `/lhg-infographic:info-select` 走决策树
- 你拿到一张别人做的图，想看看有没有硬伤时 → 跑 `/lhg-infographic:info-audit`，16 条规则先扫一遍
- 你做的图在手机上字小得看不清时 → 按 `lhg-ig-render` 的字号规范（750px 基准）重画

**什么时候不用：**

- 你只需要一张简单的截图配字 → 本插件是"生产线"，小需求直接用截图工具更快
- 你的数据涉密/未公开 → 先脱敏再画，插件不会替你审查数据合规性
- 你要的是艺术海报/插画风格的信息图 → 本插件保"准确+可读"，艺术创意需要设计师主导，插件只打辅助

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |
| [lhg-video-edit](https://github.com/lhg-plugs/lhg-video-edit) | 一句话把口播素材剪成爆款短视频（+口播脚本子命令） | `/plugin install lhg-video-edit@lhg-plugs` |
| [lhg-wechat-article](https://github.com/lhg-plugs/lhg-wechat-article) | 公众号写作专家：选题到排版一气呵成 | `/plugin install lhg-wechat-article@lhg-plugs` |
| [lhg-xiaohongshu](https://github.com/lhg-plugs/lhg-xiaohongshu) | 小红书种草专家：卖点到爆款笔记一键生成 | `/plugin install lhg-xiaohongshu@lhg-plugs` |
| [lhg-resume](https://github.com/lhg-plugs/lhg-resume) | 简历优化专家：ATS诊断到模拟面试一条龙 | `/plugin install lhg-resume@lhg-plugs` |
| [lhg-ppt](https://github.com/lhg-plugs/lhg-ppt) | PPT制作专家：述职融资答辩一键成稿 | `/plugin install lhg-ppt@lhg-plugs` |
| [lhg-excel](https://github.com/lhg-plugs/lhg-excel) | 表格数据专家：清洗透视图表一条龙 | `/plugin install lhg-excel@lhg-plugs` |
| [lhg-thesis](https://github.com/lhg-plugs/lhg-thesis) | 毕业论文助手：开题到盲审的写作流水线 | `/plugin install lhg-thesis@lhg-plugs` |
| [lhg-miniprogram](https://github.com/lhg-plugs/lhg-miniprogram) | 小程序开发专家：一句话生成微信小程序 | `/plugin install lhg-miniprogram@lhg-plugs` |
| [lhg-contract](https://github.com/lhg-plugs/lhg-contract) | 合同审查助手：风险条款标红+修改建议 | `/plugin install lhg-contract@lhg-plugs` |
| [lhg-geo](https://github.com/lhg-plugs/lhg-geo) | AI搜索优化专家：品牌在AI回答里的可见度 | `/plugin install lhg-geo@lhg-plugs` |
| [lhg-poster](https://github.com/lhg-plugs/lhg-poster) | 海报设计专家：一句话生成手机端海报 | `/plugin install lhg-poster@lhg-plugs` |
| [lhg-shopify](https://github.com/lhg-plugs/lhg-shopify) | 独立站建站专家：高转化店铺一键搭建 | `/plugin install lhg-shopify@lhg-plugs` |
| [lhg-fiction](https://github.com/lhg-plugs/lhg-fiction) | 网文写作专家：大纲到逐章+人设一致性检测 | `/plugin install lhg-fiction@lhg-plugs` |
| [lhg-drama-script](https://github.com/lhg-plugs/lhg-drama-script) | 短剧剧本专家：分集大纲到单集剧本 | `/plugin install lhg-drama-script@lhg-plugs` |
| [lhg-lit-review](https://github.com/lhg-plugs/lhg-lit-review) | 文献综述专家：框架到引用校验一条龙 | `/plugin install lhg-lit-review@lhg-plugs` |
| [lhg-salary-talk](https://github.com/lhg-plugs/lhg-salary-talk) | 薪酬谈判专家：策略到话术演练 | `/plugin install lhg-salary-talk@lhg-plugs` |
| [lhg-biz-report](https://github.com/lhg-plugs/lhg-biz-report) | 商业分析专家：数据到图文报告一键生成 | `/plugin install lhg-biz-report@lhg-plugs` |
| [lhg-study-abroad](https://github.com/lhg-plugs/lhg-study-abroad) | 留学文书专家：PS推荐信多轮打磨 | `/plugin install lhg-study-abroad@lhg-plugs` |
| [lhg-meal-plan](https://github.com/lhg-plugs/lhg-meal-plan) | 营养食谱专家：测算到一周食谱+采购单 | `/plugin install lhg-meal-plan@lhg-plugs` |
| [lhg-book-translate](https://github.com/lhg-plugs/lhg-book-translate) | 书籍翻译专家：术语锁定→章节翻译→一致性审计→译者体润色 | `/plugin install lhg-book-translate@lhg-plugs` |
| [lhg-infographic](https://github.com/lhg-plugs/lhg-infographic) | 信息图表专家：数据→选型→Canvas 绘制→手机端可读性审计 | `/plugin install lhg-infographic@lhg-plugs` |
| *（后续插件在此追加，保持表格格式一致）* | | |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、16 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-infographic/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
