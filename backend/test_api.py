import requests
import json
from datetime import date, timedelta

today = date.today()

payload = {
    "flights": [
        {
            "flight_no": "CA1001",
            "departure_city": "北京",
            "arrival_city": "上海",
            "departure_date": (today + timedelta(days=1)).isoformat(),
            "base_price": 800,
            "discount_rate": 0.1
        },
        {
            "flight_no": "CA1002",
            "departure_city": "北京",
            "arrival_city": "上海",
            "departure_date": (today + timedelta(days=3)).isoformat(),
            "base_price": 1000,
            "discount_rate": 0.15
        }
    ],
    "hotels": [
        {
            "hotel_id": "HTL001",
            "hotel_name": "上海酒店1",
            "city": "上海",
            "check_in_date": (today + timedelta(days=1)).isoformat(),
            "check_out_date": (today + timedelta(days=4)).isoformat(),
            "daily_price": 500,
            "discount_rate": 0.1
        },
        {
            "hotel_id": "HTL002",
            "hotel_name": "上海酒店2",
            "city": "上海",
            "check_in_date": (today + timedelta(days=3)).isoformat(),
            "check_out_date": (today + timedelta(days=6)).isoformat(),
            "daily_price": 600,
            "discount_rate": 0.15
        }
    ],
    "time_window": {
        "earliest_departure": today.isoformat(),
        "latest_return": (today + timedelta(days=15)).isoformat(),
        "min_stay_days": 1,
        "max_stay_days": 7
    },
    "top_n": 5,
    "price_weight": 0.5,
    "discount_weight": 0.5
}

print("=== 测试1: POST /api/v1/packages/visualization ===")
try:
    response = requests.post(
        "http://localhost:8000/api/v1/packages/visualization",
        json=payload,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"可视化数据点数: {len(data.get('scatter_data', []))}")
    print(f"候选组合总数: {data.get('total_candidates', 0)}")
    print(f"无冲突组合数: {data.get('conflict_free_count', 0)}")
    if 'scatter_data' in data and len(data['scatter_data']) > 0:
        print(f"第一个数据点: {json.dumps(data['scatter_data'][0], indent=2, default=str)}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试2: POST /api/v1/packages/recommend ===")
try:
    response = requests.post(
        "http://localhost:8000/api/v1/packages/recommend",
        json=payload,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"推荐套餐数: {len(data.get('recommendations', []))}")
    print(f"候选总数: {data.get('total_candidates', 0)}")
    if 'recommendations' in data and len(data['recommendations']) > 0:
        print(f"第一个推荐: {json.dumps(data['recommendations'][0], indent=2, default=str)}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试3: POST /api/v1/packages/sample ===")
try:
    response = requests.post(
        "http://localhost:8000/api/v1/packages/sample",
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"示例航班数: {len(data.get('flights', []))}")
    print(f"示例酒店数: {len(data.get('hotels', []))}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 所有 API 测试完成 ===")
