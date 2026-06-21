# Debug Session: matrix-index-error

**Status**: [OPEN]
**Bug Description**: 用户点击时后端抛出 IndexError 矩阵索引越界错误，网页空白
**Created**: 2026-06-21

---

## Hypotheses

1. **H1: `optimizer.py` 中 `pareto_optimal_filter` 函数的双层循环边界条件错误** - 当 DataFrame 为空或只有单行时，数组索引越界
2. **H2: `pricing.py` 中 `build_candidate_matrix` 函数在处理极端输入时产生空 DataFrame** - 后续函数未做空值检查直接访问索引
3. **H3: `normalize_scores` 函数中当 price_max == price_min 或 discount_max == discount_min 时产生除以零或 NaN** - 导致后续矩阵操作索引越界
4. **H4: `solve_multi_objective_packages` 中 `head(top_n)` 后索引重置问题** - 当结果行数少于 top_n 时越界
5. **H5: 航班/酒店日期范围不匹配导致候选组合为 0** - 后续函数未做防御性检查

---

## Evidence Log

| Step | Timestamp | Evidence | Conclusion |
|------|-----------|----------|------------|
| 1 | - | - | - |

---

## Fix Summary

待补充...
