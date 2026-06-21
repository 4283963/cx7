import sys
sys.path.insert(0, '.')

from app.engine.pricing import build_candidate_matrix, apply_fuel_surge, get_airline_code
from app.engine.optimizer import solve_multi_objective_packages
from app.schemas import FlightInfo, HotelInfo, FuelSurgeConfig
import datetime

print("=" * 60)
print("直接测试引擎 - 燃油费突增功能")
print("=" * 60)

flights = [
    FlightInfo(
        flight_no="CA1234",
        airline="中国国航",
        departure_city="北京",
        arrival_city="上海",
        departure_date="2024-06-05",
        return_date="2024-06-08",
        base_price=1500.0,
        discount_rate=0.1,
        departure_time="08:00",
        arrival_time="10:30"
    ),
    FlightInfo(
        flight_no="MU5678",
        airline="东方航空",
        departure_city="北京",
        arrival_city="上海",
        departure_date="2024-06-05",
        return_date="2024-06-08",
        base_price=1400.0,
        discount_rate=0.15,
        departure_time="09:00",
        arrival_time="11:30"
    ),
]

hotels = [
    HotelInfo(
        hotel_id=1,
        hotel_name="测试酒店",
        city="上海",
        check_in_date="2024-06-05",
        check_out_date="2024-06-08",
        daily_rates=[600.0, 600.0, 600.0],
        discount_rate=0.1
    ),
]

print("\n1. 测试航空公司代码提取:")
for f in flights:
    print(f"  {f.flight_no} -> {get_airline_code(f.flight_no)}")

print("\n2. 测试燃油费突增应用 (CA航空, +200%):")
fuel_surge = FuelSurgeConfig(
    enabled=True,
    target_airline="CA",
    price_increase_rate=2.0,
    apply_on_booking=True
)

for f in flights:
    surged, applied, original = apply_fuel_surge(f, fuel_surge)
    print(f"  {f.flight_no}: 原价={original:.0f}, 新价={surged.base_price:.0f}, 应用={applied}")

print("\n3. 测试完整候选矩阵构建:")
candidates = build_candidate_matrix(flights, hotels, fuel_surge=fuel_surge)
print(f"  候选数量: {len(candidates)}")
for i, row in candidates.iterrows():
    print(f"  {row['flight_no']}: 折扣总价=¥{row['discounted_total_price']:.0f}, "
          f"燃油费={row['fuel_surge_applied']}, "
          f"原价={row['base_price_before_surge']}")

print("\n4. 测试多目标优化:")
result = solve_multi_objective_packages(
    candidates=candidates,
    top_n=5,
    price_weight=0.5,
    discount_weight=0.5
)
print(f"  推荐数量: {len(result.recommendations)}")
for pkg in result.recommendations:
    print(f"  #{pkg.rank} {pkg.flight.flight_no}: ¥{pkg.discounted_total_price:.0f} "
          f"(折扣率{(pkg.total_discount_rate*100):.1f}%) "
          f"燃油费={pkg.fuel_surge_applied}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
