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

### 已修复的问题

#### 1. **问题1：无列空 DataFrame（H2 - 高风险）** ✅ FIXED
**位置**：[pricing.py](file:///Users/kl/Documents/trae_projects2/cx7/backend/app/engine/pricing.py#L134-L160)
**问题**：当 `flights=[]` 或 `hotels=[]` 时，`pd.DataFrame([])` 创建无列的空 DataFrame，导致后续列访问出错。
**修复**：
- 定义 `REQUIRED_COLUMNS` 常量，确保空 DataFrame 始终包含完整列结构
- 空 DataFrame 时，显式创建带有正确列的 DataFrame
- 检查并填充缺失的列

#### 2. **问题2：NaN 传播（H3 - 中风险）** ✅ FIXED
**位置**：[optimizer.py](file:///Users/kl/Documents/trae_projects2/cx7/backend/app/engine/optimizer.py#L24-L81)
**问题**：`normalize_scores` 缺少空 DataFrame 检查，`.min()`/`.max()` 可能返回 NaN 导致后续异常。
**修复**：
- 添加空 DataFrame 检查，提前返回并初始化 norm 列
- 添加列存在性检查，缺失列时抛出明确错误
- 添加 NaN 检测，对 NaN 情况设置默认值
- 使用 `.fillna()` 确保最终结果无 NaN

#### 3. **问题3：数组索引越界（H1 - 中风险）** ✅ FIXED
**位置**：[optimizer.py](file:///Users/kl/Documents/trae_projects2/cx7/backend/app/engine/optimizer.py#L104-L177)
**问题**：`pareto_optimal_filter` 中 `prices[i]`/`discounts[i]` 缺少边界检查，数组长度可能与 DataFrame 不一致。
**修复**：
- 添加空 DataFrame 检查，提前返回并初始化 `is_pareto_optimal` 列
- 添加列存在性检查
- 验证数组长度与 DataFrame 长度一致，不一致时抛出明确的 IndexError
- 移除有风险的条件索引访问（`if i < len(prices)`），改为先验证再访问

#### 4. **问题4：列缺失检查不足（新增 - 中风险）** ✅ FIXED
**位置**：[optimizer.py](file:///Users/kl/Documents/trae_projects2/cx7/backend/app/engine/optimizer.py#L180-L295)
**问题**：主入口函数缺少关键列存在性检查，列缺失会导致难以调试的 KeyError。
**修复**：
- 在 `solve_multi_objective_packages` 中添加完整的列存在性检查
- 在 `get_all_candidates_for_visualization` 中添加完整的列存在性检查
- 添加详细的调试日志，便于问题定位

### 验证结果

| 测试场景 | 测试用例 | 结果 |
|---------|---------|------|
| 边界测试1 | 航班=1, 酒店=1, 有冲突 | ✅ 通过 |
| 边界测试2 | 所有价格和折扣都相同 | ✅ 通过 |
| 边界测试3 | 索引不连续的 DataFrame | ✅ 通过 |
| 边界测试4 | 有列但没有行的 DataFrame | ✅ 通过 |
| 边界测试5 | 与前端相同的调用流程 | ✅ 通过 |
| API 测试1 | POST /api/v1/packages/visualization | ✅ 通过（200 OK） |
| API 测试2 | POST /api/v1/packages/recommend | ✅ 通过（200 OK） |
| API 测试3 | POST /api/v1/packages/sample | ✅ 通过（200 OK） |

### 防御性编程增强

1. **早失败（Fail Fast）**：在函数入口进行完整性检查，尽早发现问题
2. **明确错误**：列缺失时抛出 KeyError，数组长度不一致时抛出 IndexError，便于调试
3. **完整日志**：所有关键路径都有调试日志，包括函数入口、参数、分支决策、出口状态
4. **默认值处理**：NaN 和除零情况都有合理的默认值处理
5. **空值安全**：所有空 DataFrame 情况都有显式处理，确保列结构完整

### Bug 状态
**Status**: [FIXED]  
**Root Cause**: 推荐矩阵初始化时未确保列结构完整性，双层循环缺少数组长度一致性验证，极端边界条件下触发 IndexError。  
**Fix Applied**: 2026-06-21  
**Verified**: ✅ 所有测试通过
