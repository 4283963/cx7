from datetime import date, timedelta
from app.schemas import FlightInfo, HotelInfo, TimeWindow
from app.engine.pricing import build_candidate_matrix
from app.engine.optimizer import solve_multi_objective_packages, get_all_candidates_for_visualization
import numpy as np

time_window = TimeWindow(
    earliest_departure=date(2026,6,20), latest_return=date(2026,7,5),
    min_stay_days=2, max_stay_days=5
)

# 测试1：所有组合都有时间冲突
print('=== 测试1：所有组合都有冲突 ===')
try:
    flights = [
        FlightInfo(flight_no='CA1001', departure_city='北京', arrival_city='上海', 
                   departure_date=date(2026,6,20), base_price=800, discount_rate=0.1)
    ]
    hotels = [
        HotelInfo(hotel_id='HTL001', hotel_name='酒店', city='上海',
                  check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
                  daily_price=600, discount_rate=0.1)
    ]
    df = build_candidate_matrix(flights, hotels, time_window)
    print(f'候选矩阵形状: {df.shape}')
    print(f'列名: {df.columns.tolist()}')
    print(f'冲突自由的数量: {(df["conflict_free"]==True).sum()}')
    result, total = solve_multi_objective_packages(df)
    print(f'结果数量: {len(result)}, 候选总数: {total}')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试2：空航班列表
print('\n=== 测试2：空航班列表 ===')
try:
    df = build_candidate_matrix([], hotels, time_window)
    print(f'空输入矩阵形状: {df.shape}')
    print(f'是否为空: {df.empty}')
    print(f'列名: {df.columns.tolist() if not df.empty else "无列"}')
    result, total = solve_multi_objective_packages(df)
    print(f'结果数量: {len(result)}, 候选总数: {total}')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试3：退房日期早于入住日期（stay_days为负）
print('\n=== 测试3：stay_days为负数 ===')
try:
    flights = [
        FlightInfo(flight_no='CA1001', departure_city='北京', arrival_city='上海', 
                   departure_date=date(2026,6,25), base_price=800, discount_rate=0.1)
    ]
    hotels = [
        HotelInfo(hotel_id='HTL001', hotel_name='酒店', city='上海',
                  check_in_date=date(2026,6,28), check_out_date=date(2026,6,25),
                  daily_price=600, discount_rate=0.1)
    ]
    df = build_candidate_matrix(flights, hotels, time_window)
    print(f'stay_days的值: {df["stay_days"].values}')
    print(f'original_total_price的值: {df["original_total_price"].values}')
    result, total = solve_multi_objective_packages(df)
    print(f'结果数量: {len(result)}, 候选总数: {total}')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试4：0价格（除以零风险）
print('\n=== 测试4：0价格输入 ===')
try:
    flights = [
        FlightInfo(flight_no='CA1001', departure_city='北京', arrival_city='上海', 
                   departure_date=date(2026,6,25), base_price=0, discount_rate=0.1)
    ]
    hotels = [
        HotelInfo(hotel_id='HTL001', hotel_name='酒店', city='上海',
                  check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
                  daily_price=0, discount_rate=0.1)
    ]
    df = build_candidate_matrix(flights, hotels, time_window)
    print(f'discounted_total_price: {df["discounted_total_price"].values}')
    print(f'total_discount_rate: {df["total_discount_rate"].values}')
    result, total = solve_multi_objective_packages(df)
    print(f'结果数量: {len(result)}, 候选总数: {total}')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试5：pareto_optimal_filter 边界 - 只有1行
print('\n=== 测试5：pareto_optimal_filter 单行 ===')
try:
    import pandas as pd
    df_single = pd.DataFrame({
        'discounted_total_price': [1000],
        'total_discount_rate': [0.1]
    })
    from app.engine.optimizer import pareto_optimal_filter
    result = pareto_optimal_filter(df_single)
    print(f'单行测试通过，结果: {result}')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试6：normalize_scores 边界 - 所有价格相同
print('\n=== 测试6：normalize_scores 所有价格相同 ===')
try:
    import pandas as pd
    from app.engine.optimizer import normalize_scores
    df_same = pd.DataFrame({
        'discounted_total_price': [1000, 1000, 1000],
        'total_discount_rate': [0.1, 0.1, 0.1]
    })
    result = normalize_scores(df_same)
    print(f'price_norm: {result["price_norm"].values}')
    print(f'discount_norm: {result["discount_norm"].values}')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试7：模拟实际用户点击的场景 - 航班和酒店数量都很小
print('\n=== 测试7：航班=1, 酒店=1 ===')
try:
    flights = [
        FlightInfo(flight_no='CA1001', departure_city='北京', arrival_city='上海', 
                   departure_date=date(2026,6,25), base_price=800, discount_rate=0.15)
    ]
    hotels = [
        HotelInfo(hotel_id='HTL001', hotel_name='上海酒店', city='上海',
                  check_in_date=date(2026,6,25), check_out_date=date(2026,6,28),
                  daily_price=600, discount_rate=0.1)
    ]
    df = build_candidate_matrix(flights, hotels, time_window)
    print(f'候选数: {len(df)}')
    viz_data = get_all_candidates_for_visualization(df)
    print(f'可视化数据: {len(viz_data)} 条')
    result, total = solve_multi_objective_packages(df, top_n=5)
    print(f'推荐结果: {len(result)} 条')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试8：航班=2, 酒店=10
print('\n=== 测试8：航班=2, 酒店=10 ===')
try:
    flights = []
    for i in range(2):
        flights.append(FlightInfo(
            flight_no=f'CA{i+1}001', departure_city='北京', arrival_city='上海',
            departure_date=date(2026,6,25+i), base_price=800+i*100, discount_rate=0.1+i*0.05
        ))
    hotels = []
    for i in range(10):
        check_in = date(2026,6,25) + timedelta(days=i)
        check_out = check_in + timedelta(days=2)
        hotels.append(HotelInfo(
            hotel_id=f'HTL{i+1:03d}', hotel_name=f'酒店{i+1}', city='上海',
            check_in_date=check_in, check_out_date=check_out,
            daily_price=500+i*50, discount_rate=0.05+i*0.01
        ))
    df = build_candidate_matrix(flights, hotels, time_window)
    print(f'候选矩阵: {df.shape}')
    print(f'有效候选: {(df["conflict_free"]==True).sum()}')
    viz_data = get_all_candidates_for_visualization(df)
    print(f'可视化数据: {len(viz_data)} 条')
    result, total = solve_multi_objective_packages(df, top_n=5)
    print(f'推荐结果: {len(result)} 条')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

# 测试9：检查 build_candidate_matrix 在 flights=[], hotels=[] 时
print('\n=== 测试9：flights=[], hotels=[] ===')
try:
    df = build_candidate_matrix([], [], time_window)
    print(f'空矩阵形状: {df.shape}')
    print(f'列名: {df.columns.tolist() if not df.empty else "EMPTY - NO COLUMNS"}')
    print(f'df.empty: {df.empty}')
    # 测试后续处理
    result, total = solve_multi_objective_packages(df)
    print(f'solve结果: {len(result)}')
    viz_data = get_all_candidates_for_visualization(df)
    print(f'viz结果: {len(viz_data)}')
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()

print('\n=== 所有测试完成 ===')
