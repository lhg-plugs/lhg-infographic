#!/usr/bin/env python3
"""lhg-infographic 硬门②：chart-spec.json 写入后，若数据来源未标注则提醒。

触发：PostToolUse / Write|Edit。只关心 chart-spec*.json 文件，
其他文件 0 开销直接放行。

逻辑：spec 文件写入后，检查其 source 字段；若为空，则追加一条
additionalContext 提醒标注数据来源（没来源的图就是一张漂亮的谣言）。

逃生方式（按推荐度排序）：
  1. 按提醒补上 source（推荐）。
  2. 紧急情况：LHG_INFOGRAPHIC_HOOKS_OFF=1（单次豁免本次 hook）。
  3. /plugin disable lhg-infographic（整个插件停用，hooks 不再触发）。

设计原则：任何内部出错（找不到文件、解析失败等）都 fail-open 静默放行，
绝不因提醒脚本自身故障打断绘制；本 hook 只提醒、不拦截。
零第三方依赖。
"""

import json
import os
import sys


def main() -> int:
    # 逃生开关
    if os.environ.get("LHG_INFOGRAPHIC_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""

    # 只关心 chart-spec 文件
    base = os.path.basename(file_path.replace("\\", "/"))
    if not (base.startswith("chart-spec") and base.endswith(".json")):
        return 0

    try:
        with open(file_path, encoding="utf-8") as f:
            spec = json.load(f)
    except Exception:
        return 0  # 解析失败：fail-open

    if isinstance(spec, dict) and str(spec.get("source", "")).strip():
        return 0

    msg = (
        "lhg-infographic 提醒：%s 的 source（数据来源）为空。"
        "没来源的图就是一张漂亮的谣言，建议补上三要素："
        "数据来源 / 统计口径 / 时间范围；确认暂不标注可忽略本提醒。"
        % base
    )
    sys.stdout.write(json.dumps({"additionalContext": msg}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
