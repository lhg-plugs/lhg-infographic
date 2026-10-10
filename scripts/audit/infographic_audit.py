#!/usr/bin/env python3
"""lhg-infographic 确定性信息图审计：16 条规则，零第三方依赖。

扫描信息图项目目录下的 chart-spec*.json（图表规格文件），检查
标题与来源、数据-图表映射、字号、颜色对比、数据完整性。

用法：
    python3 infographic_audit.py --target <项目目录> [--format json|text]
                                 [--fail-on blocker|warning|nit]

有 >= fail-on 级别发现时以 exit code 2 退出（供 hooks 与 CI 使用）。

规则文案均为本项目原创；对比度公式采用 WCAG 2.x 相对亮度定义
（W3C 公开标准），实现为独立编写；字号阈值以 750px 设计稿为基准，
详见 lhg-ig-review skill。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-infographic/infographic-audit"

# 字号阈值（750px 设计稿基准，启发值）
MIN_FONT_PX = 20          # 最小字号硬门（blocker）
TITLE_GAP_PX = 4          # 标题与标签字号最小差距
# 对比度阈值（WCAG 2.x 相对亮度公式）
CONTRAST_WARN = 4.5
CONTRAST_BLOCKER = 3.0
SERIES_CONTRAST_WARN = 1.3
PIE_MAX_SECTORS = 6
BAR_MAX_CATEGORIES = 12
UNIT_HINTS = ("万", "亿", "%", "元", "件", "人", "次", "倍", "kg", "km")


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file",
                 "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line,
                 snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity, "category": category,
             "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


# ---------------- 颜色工具（WCAG 2.x 相对亮度，公开标准公式） ----------------

def _parse_hex(h):
    h = str(h).strip().lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{3}", h):
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError("非法颜色值：%s" % h)
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rel_luminance(rgb):
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(h1, h2):
    l1, l2 = _rel_luminance(_parse_hex(h1)), _rel_luminance(_parse_hex(h2))
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


class Spec:
    def __init__(self, path, rel):
        self.path = path
        self.rel = rel
        self.data = {}
        self.ok = False
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                self.data = d
                self.ok = True
        except Exception:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)


def load_specs(target):
    specs = []
    for fn in sorted(os.listdir(target)):
        if fn.startswith("chart-spec") and fn.endswith(".json"):
            p = os.path.join(target, fn)
            if os.path.isfile(p):
                specs.append(Spec(p, fn))
    return specs


# ---------------- 标题与来源 ----------------

@rule("IG-TITLE-001", "blocker", "标题", "图表标题缺失",
      "标题缺失或过短（< 4 字）。没标题的图不许交付。")
def check_title(spec, emit):
    title = str(spec.get("title", "") or "").strip()
    if len(title) < 4:
        emit("IG-TITLE-001", spec.rel, 0, title,
             "标题缺失或过短（当前 %d 字），请写一句人话标题"
             % len(title))


@rule("IG-SOURCE-001", "warning", "来源", "数据来源未标注",
      "source 为空。没来源的图就是一张漂亮的谣言。")
def check_source(spec, emit):
    src = str(spec.get("source", "") or "").strip()
    if not src:
        emit("IG-SOURCE-001", spec.rel, 0, "",
             "数据来源未标注，建议补三要素：来源 / 统计口径 / 时间范围")


# ---------------- 数据-图表映射 ----------------

@rule("IG-MAP-001", "blocker", "映射", "饼图表达时间趋势",
      "chart_type=pie 但 data_shape=time_series：扇形表达不了时间先后，请换折线图。")
def check_pie_trend(spec, emit):
    if (str(spec.get("chart_type", "")).lower() == "pie"
            and str(spec.get("data_shape", "")).lower() == "time_series"):
        emit("IG-MAP-001", spec.rel, 0, "",
             "饼图用于时间趋势数据，方向性错误：请换折线图（line）")


@rule("IG-MAP-002", "blocker", "映射", "折线图用于无序分类",
      "chart_type=line 但 data_shape=categorical_nominal：折线斜率暗示了不存在的连续变化，请换柱状图。")
def check_line_nominal(spec, emit):
    if (str(spec.get("chart_type", "")).lower() == "line"
            and str(spec.get("data_shape", "")).lower()
            == "categorical_nominal"):
        emit("IG-MAP-002", spec.rel, 0, "",
             "折线图用于无序分类数据，方向性错误：请换柱状图（bar）")


@rule("IG-MAP-003", "warning", "映射", "饼图扇区过多",
      "饼图扇区超过 6 个就是色块拼盘，请合并小类为“其他”或换条形图。")
def check_pie_sectors(spec, emit):
    if str(spec.get("chart_type", "")).lower() == "pie":
        n = len(spec.get("data", []) or [])
        if n > PIE_MAX_SECTORS:
            emit("IG-MAP-003", spec.rel, 0, "",
                 "饼图 %d 个扇区（上限 %d），请合并小类或换横向条形图"
                 % (n, PIE_MAX_SECTORS))


@rule("IG-MAP-004", "warning", "映射", "柱状图类别过多",
      "柱状图类别超过 12 个，手机上会缩成牙签，请聚合或拆图。")
def check_bar_categories(spec, emit):
    if str(spec.get("chart_type", "")).lower() == "bar":
        n = len(spec.get("data", []) or [])
        if n > BAR_MAX_CATEGORIES:
            emit("IG-MAP-004", spec.rel, 0, "",
                 "柱状图 %d 个类别（上限 %d），请聚合或拆图"
                 % (n, BAR_MAX_CATEGORIES))


@rule("IG-MAP-005", "warning", "映射", "柱状图 Y 轴不从 0 起",
      "柱状图 Y 轴不从 0 起且未标注截断：条形长度代表数值，截断即视觉欺诈。")
def check_bar_baseline(spec, emit):
    if str(spec.get("chart_type", "")).lower() == "bar":
        if not spec.get("y_starts_at_zero", True) and not str(
                spec.get("baseline_note", "") or "").strip():
            emit("IG-MAP-005", spec.rel, 0, "",
                 "柱状图 Y 轴不从 0 起：请改回从 0 起，或在图上明确标注“Y 轴截断”")


# ---------------- 字号 ----------------

def _min_font(spec):
    fonts = spec.get("fonts", {}) or {}
    vals = []
    for v in fonts.values():
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            pass
    return min(vals) if vals else None


@rule("IG-FONT-001", "blocker", "字号", "最小字号过小",
      "750px 基准下最小字号 < 20px，手机端不可读。")
def check_min_font(spec, emit):
    mf = _min_font(spec)
    if mf is not None and mf < MIN_FONT_PX:
        emit("IG-FONT-001", spec.rel, 0, "",
             "最小字号 %.0fpx（硬门 %dpx），手机端不可读，请放大"
             % (mf, MIN_FONT_PX))


@rule("IG-FONT-002", "warning", "字号", "标题与正文字号层级不清",
      "标题字号 <= 标签字号，视觉层级塌掉，三级字号至少拉开 4px。")
def check_font_hierarchy(spec, emit):
    fonts = spec.get("fonts", {}) or {}
    try:
        t, l = float(fonts["title"]), float(fonts["label"])
    except (KeyError, TypeError, ValueError):
        return
    if t - l < TITLE_GAP_PX:
        emit("IG-FONT-002", spec.rel, 0, "",
             "标题 %.0fpx / 标签 %.0fpx（差距应 ≥ %dpx），层级不清请拉开"
             % (t, l, TITLE_GAP_PX))


# ---------------- 颜色 ----------------

@rule("IG-COLOR-001", "warning", "颜色", "文字/背景对比不足",
      "对比度 < 4.5 警告、< 3.0 blocker（WCAG 2.x 相对亮度公式）。")
def check_text_contrast(spec, emit):
    colors = spec.get("colors", {}) or {}
    bg, tx = colors.get("background"), colors.get("text")
    if not bg or not tx:
        return
    try:
        cr = contrast_ratio(bg, tx)
    except ValueError as e:
        emit("IG-COLOR-001", spec.rel, 0, "",
             "颜色值无法解析：%s" % e)
        return
    if cr < CONTRAST_BLOCKER:
        _RULE_BY_ID["IG-COLOR-001"]["_severity_override"] = "blocker"
        emit("IG-COLOR-001", spec.rel, 0, "",
             "文字/背景对比度 %.2f（< %.1f），严重不可读，请加深文字或调浅背景"
             % (cr, CONTRAST_BLOCKER))
        _RULE_BY_ID["IG-COLOR-001"].pop("_severity_override", None)
    elif cr < CONTRAST_WARN:
        emit("IG-COLOR-001", spec.rel, 0, "",
             "文字/背景对比度 %.2f（< %.1f），建议加深文字或调浅背景"
             % (cr, CONTRAST_WARN))


@rule("IG-COLOR-002", "warning", "颜色", "相邻系列色难区分",
      "相邻系列色对比度 < 1.3，肉眼分不开；禁红绿搭配。")
def check_series_colors(spec, emit):
    colors = spec.get("colors", {}) or {}
    series = colors.get("series", []) or []
    for i in range(len(series) - 1):
        try:
            cr = contrast_ratio(series[i], series[i + 1])
        except ValueError:
            continue
        if cr < SERIES_CONTRAST_WARN:
            emit("IG-COLOR-002", spec.rel, 0, "",
                 "系列色 %d/%d 对比度 %.2f（< %.1f），肉眼难区分请换色"
                 % (i + 1, i + 2, cr, SERIES_CONTRAST_WARN))


# ---------------- 数据 ----------------

def _data_rows(spec):
    data = spec.get("data", None)
    if not isinstance(data, list):
        return None
    return data


@rule("IG-DATA-001", "blocker", "数据", "数据为空",
      "data 为空或不是列表。空数据画什么图。")
def check_data_empty(spec, emit):
    rows = _data_rows(spec)
    if not rows:
        emit("IG-DATA-001", spec.rel, 0, "",
             "data 为空：请先整理数据再选型绘制")


@rule("IG-DATA-002", "blocker", "数据", "标签与数值不匹配",
      "data 行缺 label 或 value 字段，或 value 不是数字。")
def check_data_shape(spec, emit):
    rows = _data_rows(spec)
    if not rows:
        return
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or "label" not in r or "value" not in r:
            emit("IG-DATA-002", spec.rel, 0, "",
                 "data 第 %d 行缺 label/value 字段" % (i + 1))
            return
        try:
            float(r["value"])
        except (TypeError, ValueError):
            emit("IG-DATA-002", spec.rel, 0, "",
                 "data 第 %d 行 value 不是数字：%r" % (i + 1, r["value"]))
            return


@rule("IG-DATA-003", "warning", "数据", "饼图百分比总和不为 100",
      "饼图 value 疑似百分比但总和 ≠ 100（±1），数据自相矛盾。")
def check_pie_sum(spec, emit):
    if str(spec.get("chart_type", "")).lower() != "pie":
        return
    rows = _data_rows(spec)
    if not rows:
        return
    vals = []
    for r in rows:
        try:
            vals.append(float(r.get("value", 0)))
        except (TypeError, ValueError):
            return
    if vals and all(v <= 100 for v in vals):
        s = sum(vals)
        if abs(s - 100) > 1:
            emit("IG-DATA-003", spec.rel, 0, "",
                 "饼图数值总和为 %.1f（应 ≈ 100），请核对数据" % s)


@rule("IG-LABEL-001", "warning", "数据", "坐标轴标签缺失",
      "折线/柱状图缺 x_label 或 y_label，读者不知道轴代表什么。")
def check_axis_labels(spec, emit):
    if str(spec.get("chart_type", "")).lower() in ("line", "bar"):
        missing = [k for k in ("x_label", "y_label")
                   if not str(spec.get(k, "") or "").strip()]
        if missing:
            emit("IG-LABEL-001", spec.rel, 0, "",
                 "坐标轴标签缺失：%s" % "、".join(missing))


@rule("IG-UNIT-001", "nit", "数据", "数值单位未声明",
      "数值较大但 y_label 无单位提示，建议标注单位。")
def check_unit(spec, emit):
    if str(spec.get("chart_type", "")).lower() not in ("line", "bar"):
        return
    rows = _data_rows(spec)
    if not rows:
        return
    vals = []
    for r in rows:
        try:
            vals.append(float(r.get("value", 0)))
        except (TypeError, ValueError):
            return
    y_label = str(spec.get("y_label", "") or "")
    if vals and max(vals) >= 10000 and not any(
            u in y_label for u in UNIT_HINTS):
        emit("IG-UNIT-001", spec.rel, 0, "",
             "最大值 %g 但 y_label「%s」无单位提示，建议标注单位"
             % (max(vals), y_label or "（空）"))


# ---------------- 主流程 ----------------

def run(target):
    specs = load_specs(target)
    findings = []

    def emit(rule_id, file, line, snippet, detail):
        r = _RULE_BY_ID[rule_id]
        sev = r.get("_severity_override", r["severity"])
        findings.append(Finding(rule_id, sev, r["category"],
                                r["title"], file, line, snippet, detail))

    for spec in specs:
        if not spec.ok:
            findings.append(Finding("IG-DATA-001", "blocker", "数据",
                                    "spec 文件无法解析", spec.rel, 0, "",
                                    "chart-spec JSON 解析失败，请检查格式"))
            continue
        for r in RULES:
            try:
                r["check"](spec, emit)
            except Exception as e:
                findings.append(Finding(
                    r["id"], "nit", "脚本", "规则执行异常",
                    "infographic_audit.py", 0, "",
                    "规则 %s 执行出错：%s（已跳过）" % (r["id"], e)))
    return specs, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="lhg-infographic 信息图审计")
    ap.add_argument("--target", default=".", help="信息图项目目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"],
                    default="blocker")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print("target 不是目录：%s" % args.target, file=sys.stderr)
        return 1

    specs, findings = run(target)
    sev_rank = {"blocker": 3, "warning": 2, "nit": 1}
    counts = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    result = {
        "tool": TOOL,
        "version": VERSION,
        "target": args.target,
        "summary": {
            "specs_scanned": len(specs),
            "rules_run": len(RULES),
            "blocker": counts["blocker"],
            "warning": counts["warning"],
            "nit": counts["nit"],
        },
        "findings": [f.to_dict() for f in sorted(
            findings, key=lambda x: (-sev_rank.get(x.severity, 0),
                                     x.file, x.line))],
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print("信息图审计：扫描 %d 个 spec，运行 %d 条规则" % (
            s["specs_scanned"], s["rules_run"]))
        print("blocker=%d warning=%d nit=%d" % (
            s["blocker"], s["warning"], s["nit"]))
        for f in result["findings"]:
            print("[%s][%s] %s:%d %s" % (
                f["severity"].upper(), f["rule_id"], f["file"],
                f["line"], f["title"]))
            print("    %s" % f["detail"])
            if f["snippet"]:
                print("    → %s" % f["snippet"])

    level = sev_rank[args.fail_on]
    bad = any(sev_rank.get(f.severity, 0) >= level for f in findings)
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
