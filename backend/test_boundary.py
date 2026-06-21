from datetime import date, timedelta
from app.schemas import FlightInfo, HotelInfo, TimeWindow
from app.engine.pricing import build_candidate_matrix
from app.engine.optimizer import solve_multi_objective_packages, get_all_candidates_for_visualization
import numpy as np
import pandas as pd

time_window = TimeWindow(
    earliest_departure=date(2026,6,20), latest_return=date(2026,7,5),
    min_stay_days=1, max_stay_days=7
)

# 测试1：航班=1, 酒店=1, 但有冲突
print('=== 测试1：航班=1, 酒店=1, 有冲突 ===')
flights = [FlightInfo(flight_no='CA1001', departure_city='北京', arrival_city='上海', 
                      departure_date=date(2026,6,20), base_price=800, discount_rate=0.1)]
hotels = [HotelInfo(hotel_id='HTL001', hotel_name='酒店', city='上海',
                    check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
                    daily_price=600, discount_rate=0.1)]
df = build_candidate_matrix(flights, hotels, time_window)
print(f'df.shape={df.shape}, df.empty={df.empty}')
print(f'conflict_free counts: {df["conflict_free"].value_counts().to_dict()}')
try:
    viz = get_all_candidates_for_visualization(df)
    print(f'viz len={len(viz)}')
    recs, total = solve_multi_objective_packages(df)
    print(f'recs len={len(recs)}, total={total}')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试2：所有价格和折扣都相同
print('\n=== 测试2：所有价格和折扣都相同 ===')
flights = [
    FlightInfo(flight_no='CA1001', departure_city='北京', arrival_city='上海', 
               departure_date=date(2026,6,25), base_price=1000, discount_rate=0.1),
    FlightInfo(flight_no='CA1002', departure_city='北京', arrival_city='上海', 
               departure_date=date(2026,6,25), base_price=1000, discount_rate=0.1)
]
hotels = [
    HotelInfo(hotel_id='HTL001', hotel_name='酒店', city='上海',
              check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
              daily_price=500, discount_rate=0.1),
    HotelInfo(hotel_id='HTL002', hotel_name='酒店2', city='上海',
              check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
              daily_price=500, discount_rate=0.1)
]
df = build_candidate_matrix(flights, hotels, time_window)
print(f'df.shape={df.shape}')
try:
    viz = get_all_candidates_for_visualization(df)
    print(f'viz len={len(viz)}')
    recs, total = solve_multi_objective_packages(df)
    print(f'recs len={len(recs)}')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试3：手动构造索引异常的 DataFrame
print('\n=== 测试3：索引不连续的 DataFrame ===')
flights3 = [
    FlightInfo(flight_no='CA1', departure_city='北京', arrival_city='上海', 
               departure_date=date(2026,6,25), base_price=1000, discount_rate=0.1),
    FlightInfo(flight_no='CA2', departure_city='北京', arrival_city='上海', 
               departure_date=date(2026,6,25), base_price=1000, discount_rate=0.1),
    FlightInfo(flight_no='CA3', departure_city='北京', arrival_city='上海', 
               departure_date=date(2026,6,25), base_price=1000, discount_rate=0.1)
]
hotels3 = [
    HotelInfo(hotel_id='H1', hotel_name='酒店1', city='上海',
              check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
              daily_price=500, discount_rate=0.1),
    HotelInfo(hotel_id='H2', hotel_name='酒店2', city='上海',
              check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
              daily_price=500, discount_rate=0.1),
    HotelInfo(hotel_id='H3', hotel_name='酒店3', city='上海',
              check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
              daily_price=500, discount_rate=0.1)
]
df_test = pd.DataFrame({
    'discounted_total_price': [1000, 2000, 1500],
    'total_discount_rate': [0.1, 0.2, 0.15],
    'conflict_free': [True, True, True],
    'flight_obj': flights3,
    'hotel_obj': hotels3,
    'flight_no': ['CA1', 'CA2', 'CA3'],
    'hotel_id': ['H1', 'H2', 'H3'],
    'original_total_price': [1500, 2500, 2000],
    'total_discount_amount': [150, 250, 200],
    'stay_days': [3, 3, 3]
})
df_test = df_test.drop(0)
print(f'df_test after drop index=0:')
print(df_test)
print(f'len(df_test)={len(df_test)}')
print(f'index={df_test.index.tolist()}')

from app.engine.optimizer import pareto_optimal_filter, normalize_scores
try:
    df_norm = normalize_scores(df_test)
    print(f'normalize_scores OK, shape={df_norm.shape}')
    df_pareto = pareto_optimal_filter(df_test)
    print(f'pareto_optimal_filter OK, shape={df_pareto.shape}')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试4：DataFrame 有列但没有行（过滤后）
print('\n=== 测试4：有列但没有行的 DataFrame ===')
df_empty_rows = df_test[df_test['discounted_total_price'] > 10000]
print(f'df_empty_rows.shape={df_empty_rows.shape}')
print(f'df_empty_rows.empty={df_empty_rows.empty}')
print(f'columns={df_empty_rows.columns.tolist()}')
try:
    df_norm = normalize_scores(df_empty_rows)
    print(f'normalize_scores OK, shape={df_norm.shape}')
    df_pareto = pareto_optimal_filter(df_empty_rows)
    print(f'pareto_optimal_filter OK, shape={df_pareto.shape}')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试5：最可能触发错误的场景 - 与前端相同的调用顺序
print('\n=== 测试5：与前端相同的调用流程 ===')
from app.engine.optimizer import get_all_candidates_for_visualization
try:
    df = build_candidate_matrix(flights, hotels, time_window)
    print(f'build_candidate_matrix OK, shape={df.shape}')
    
    viz_data = get_all_candidates_for_visualization(df, price_weight=0.5, discount_weight=0.5)
    print(f'get_all_candidates_for_visualization OK, len={len(viz_data)}')
    
    recs, total = solve_multi_objective_packages(df, top_n=5, price_weight=0.5, discount_weight=0.5)
    print(f'solve_multi_objective_packages OK, len={len(recs)}')
    
    print('\n测试通过，未触发 IndexError')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试6：测试 API 路由层
print('\n=== 测试6：模拟 API 调用（含异常处理） ===')
try:
    from app.api.routes import _dbg_log
    print('dbg_log 函数存在')
except Exception as e:
    print(f'注意: {e}')
