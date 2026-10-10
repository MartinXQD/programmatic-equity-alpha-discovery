# 程序化股票因子发现

本项目通过受限公式语言自动组合量价和财务字段，再用一致的本地持仓、收益与筛选规则比较候选，并整理已有 WorldQuant BRAIN 检验证据。

[English README](README.md) · [英文论文展示版](paper/Research_Paper_Public_EN.pdf) · [中文论文展示版](paper/Research_Paper_Public_CN.pdf)

## 研究流程

历史股票及财务数据 → 公式生成 → 双本地评价器 → 数据与表现筛选 → 平台表达审查 → Pareto 优先顺序与 Signal-first 重复信息审查 → BRAIN 检验 → 结果解释。

经济上合理的想法不一定表现良好。数据定义、窗口、方向和持仓方法都会影响结果，程序化搜索使这些实现选择可以被系统比较。因子机制与未来投资价值仍需要进一步验证。

## 冻结结果

截至 2026 年 10 月 7 日的完成队列证据：

| 阶段 | 数量 | 含义 |
|---|---:|---|
| 生成并完成两种本地评价 | 20,000 | 含 48 条退化但已计算的结果 |
| 进入平台表达审查 | 10,117 | 毛收益路线，包含 2,227 条成本路线合格者 |
| 当前支持近似表达 | 3,562 | 不代表本地与平台计算等价 |
| 保留且取得有效平台结果 | 3,285 | 3,237 条新有效结果，加 48 条匹配的历史复用结果 |
| 满足已记录的适用非相关性要求 | 82 | 通过率约 2.50%，相关性和提交状态分别判断 |

**82 条不等于 82 条已接受、互不相关、具备最终提交资格或已提交的 Alpha。** 其中 79 条相关性待确认、2 条明确 self-correlation 失败、1 条可见检查通过但 production correlation 未显示。全部 40 个 Pareto 层完成；277 条延期是可恢复的排程决定。

## 运行合成示例

需要 Python 3.12 或 3.13：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install '.[dev]'
pytest -q
alpha-discovery demo --output artifacts/demo
python scripts/verify_results.py
python scripts/check_internal_links.py --ref HEAD
```

示例生成完全合成的股票与年度财务数据，运行真实核心公式解释器、双评价器、质量筛选与重复信息审查。无需 WRDS 或 BRAIN 账号，示例数字不能解释为市场表现。

有合法数据权限的研究者可按照 [英文复现指南](docs/reproduction.md) 提供指定 schema 的文件。本次发布没有重跑 20,000 条历史研究，也没有重新进行 BRAIN Simulation 或提交 Alpha。实际执行与未执行的验证分别记在 [验证记录](docs/validation.md)。

## 文件与发布边界

`src/` 保存核心算法，`notebooks/` 提供三个合成教学入口，`results/` 保存经过核对的汇总结果，`docs/` 说明方法、复现和限制。

两份论文是明确标记的展示改编版，保留最终研究结论，移除真实表达式、Alpha ID 与单条平台明细；未删改的原论文保存在原始研究项目。原始 CRSP/Compustat/CCM 数据、账号、凭证、平台截图及完整候选记录均不上传。

用户已授权在完整历史审查及普通 BRAIN 用户协议核对通过后公开当前仓库；LICENSE 尚未选定。2019–2024 全部为开发期已见数据，尚未完成独立样本检验，本地实现也不等于 BRAIN 的精确复制。
