import requests
import json
from datetime import date, timedelta

today = date.today()

print("=== 测试: 预订价格变动拦截和交易降级 ===\n")

flight = {
    "flight_no": "CA1001",
    "departure_city": "北京",
    "arrival_city": "上海",
    "departure_date": (today + timedelta(days=2)).isoformat(),
    "base_price": 800,
    "discount_rate": 0.1
}

hotel = {
    "hotel_id": "HTL001",
    "hotel_name": "上海酒店1",
    "city": "上海",
    "check_in_date": (today + timedelta(days=1)).isoformat(),
    "check_out_date": (today + timedelta(days=5)).isoformat(),
    "daily_price": 500,
    "discount_rate": 0.1
}

original_flight_price = 800 * 0.9
original_hotel_price = 500 * 4 * 0.9
original_total = original_flight_price + original_hotel_price

print(f"原始价格: 机票 ¥{original_flight_price} + 酒店 ¥{original_hotel_price} = ¥{original_total}")
print(f"燃油费突增 200% 后: 机票 ¥{800 * 3 * 0.9} + 酒店 ¥{original_hotel_price} = ¥{800 * 3 * 0.9 + original_hotel_price}")
print(f"价格涨幅: {((800 * 3 * 0.9 + original_hotel_price) - original_total) / original_total * 100:.1f}%")
print()

book_payload = {
    "package_id": "PKG-001-CA1001-HTL001",
    "flight": flight,
    "hotel": hotel,
    "quoted_price": original_total,
    "fuel_surge": {
        "enabled": True,
        "target_airline": "CA",
        "price_increase_rate": 2.0,
        "apply_on_booking": True
    }
}

print("--- 测试 200% 涨幅 (DOWNGRADED 级别) ---")
response = requests.post(
    "http://localhost:8000/api/v1/packages/book",
    json=book_payload,
    timeout=10
)
result = response.json()
print(f"状态码: {response.status_code}")
print(f"成功: {result.get('success')}")
print(f"拦截级别: {result.get('intercept_level')}")
print(f"原始价格: ¥{result.get('original_price')}")
print(f"最终价格: ¥{result.get('final_price')}")
print(f"价格变动: +¥{result.get('price_change_amount'):.0f} (+{result.get('price_change_rate') * 100:.1f}%)")
print(f"消息: {result.get('message')}")
print(f"燃油费触发: {result.get('surge_triggered')}")
print(f"受影响航司: {result.get('affected_airline')}")
if result.get('downgraded_alternative'):
    alt = result['downgraded_alternative']
    print(f"降级方案: {alt.get('description')}")
    print(f"推荐航司: {alt.get('suggested_airlines')}")
print()

print("--- 测试 50% 涨幅 (WARNING 级别) ---")
book_payload_50 = book_payload.copy()
book_payload_50['fuel_surge'] = {
    "enabled": True,
    "target_airline": "CA",
    "price_increase_rate": 0.5,
    "apply_on_booking": True
}
response = requests.post(
    "http://localhost:8000/api/v1/packages/book",
    json=book_payload_50,
    timeout=10
)
result = response.json()
print(f"拦截级别: {result.get('intercept_level')}")
print(f"价格变动: +{result.get('price_change_rate') * 100:.1f}%")
print(f"消息: {result.get('message')}")
print()

print("--- 测试 300% 涨幅 (BLOCKED 级别) ---")
book_payload_300 = book_payload.copy()
book_payload_300['fuel_surge'] = {
    "enabled": True,
    "target_airline": "CA",
    "price_increase_rate": 3.0,
    "apply_on_booking": True
}
response = requests.post(
    "http://localhost:8000/api/v1/packages/book",
    json=book_payload_300,
    timeout=10
)
result = response.json()
print(f"拦截级别: {result.get('intercept_level')}")
print(f"价格变动: +{result.get('price_change_rate') * 100:.1f}%")
print(f"消息: {result.get('message')}")
print()

print("--- 测试不受影响的航司 (MU) ---")
mu_flight = flight.copy()
mu_flight['flight_no'] = "MU2001"
mu_flight['base_price'] = 900
book_payload_mu = book_payload.copy()
book_payload_mu['flight'] = mu_flight
book_payload_mu['quoted_price'] = 900 * 0.9 + 500 * 4 * 0.9
response = requests.post(
    "http://localhost:8000/api/v1/packages/book",
    json=book_payload_mu,
    timeout=10
)
result = response.json()
print(f"拦截级别: {result.get('intercept_level')}")
print(f"成功: {result.get('success')}")
print(f"消息: {result.get('message')}")
print()

print("=== 预订拦截测试完成 ===")
