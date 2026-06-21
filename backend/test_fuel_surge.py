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
            "departure_date": (today + timedelta(days=2)).isoformat(),
            "base_price": 800,
            "discount_rate": 0.1
        },
        {
            "flight_no": "MU2001",
            "departure_city": "北京",
            "arrival_city": "上海",
            "departure_date": (today + timedelta(days=2)).isoformat(),
            "base_price": 900,
            "discount_rate": 0.12
        }
    ],
    "hotels": [
        {
            "hotel_id": "HTL001",
            "hotel_name": "上海酒店1",
            "city": "上海",
            "check_in_date": (today + timedelta(days=1)).isoformat(),
            "check_out_date": (today + timedelta(days=5)).isoformat(),
            "daily_price": 500,
            "discount_rate": 0.1
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
    "discount_weight": 0.5,
    "fuel_surge": {
        "enabled": True,
        "target_airline": "CA",
        "price_increase_rate": 2.0,
        "apply_on_booking": True
    }
}

print("=== 测试1: 带燃油费突增的推荐计算 ===")
try:
    response = requests.post(
        "http://localhost:8000/api/v1/packages/visualization",
        json=payload,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"成功: {data.get('success')}")
    print(f"候选总数: {data.get('total_candidates')}")
    print(f"无冲突数: {data.get('conflict_free_count')}")
    print(f"燃油费影响数: {data.get('fuel_surge_applied_count')}")
    print(f"目标航司: {data.get('fuel_surge_target')}")
    
    all_candidates = data.get('all_candidates', [])
    for c in all_candidates:
        print(f"  {c['flight_no']}: ¥{c['discounted_total_price']} (燃油费: {c.get('fuel_surge_applied', False)})")
    
    top_pkgs = data.get('top_packages', [])
    if top_pkgs:
        print(f"\nTop 1:")
        p = top_pkgs[0]
        print(f"  {p['flight']['flight_no']} + {p['hotel']['hotel_name']}")
        print(f"  价格: ¥{p['discounted_total_price']}")
        print(f"  燃油费已应用: {p.get('fuel_surge_applied', False)}")
        if p.get('base_price_before_surge'):
            print(f"  突增前价格: ¥{p['base_price_before_surge']}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试2: 预订拦截 - 受影响航班 ===")
try:
    top_pkg = top_pkgs[0] if top_pkgs else None
    if top_pkg and top_pkg.get('fuel_surge_applied'):
        book_payload = {
            "package_id": top_pkg['package_id'],
            "flight": top_pkg['flight'],
            "hotel": top_pkg['hotel'],
            "quoted_price": top_pkg['discounted_total_price'],
            "fuel_surge": {
                "enabled": True,
                "target_airline": "CA",
                "price_increase_rate": 2.0,
                "apply_on_booking": True
            }
        }
        response = requests.post(
            "http://localhost:8000/api/v1/packages/book",
            json=book_payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"成功: {result.get('success')}")
        print(f"拦截级别: {result.get('intercept_level')}")
        print(f"原始价格: ¥{result.get('original_price')}")
        print(f"最终价格: ¥{result.get('final_price')}")
        print(f"价格变动: ¥{result.get('price_change_amount')} ({result.get('price_change_rate') * 100:.1f}%)")
        print(f"消息: {result.get('message')}")
        print(f"燃油费触发: {result.get('surge_triggered')}")
        print(f"受影响航司: {result.get('affected_airline')}")
        if result.get('downgraded_alternative'):
            print(f"降级方案: {result['downgraded_alternative']['description']}")
    else:
        print("跳过：没有受燃油费影响的套餐")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试3: 预订 - 不受影响的航班 (MU) ===")
try:
    mu_pkg = None
    for pkg in top_pkgs:
        if 'MU' in pkg['flight']['flight_no']:
            mu_pkg = pkg
            break
    
    if mu_pkg:
        book_payload = {
            "package_id": mu_pkg['package_id'],
            "flight": mu_pkg['flight'],
            "hotel": mu_pkg['hotel'],
            "quoted_price": mu_pkg['discounted_total_price'],
            "fuel_surge": {
                "enabled": True,
                "target_airline": "CA",
                "price_increase_rate": 2.0,
                "apply_on_booking": True
            }
        }
        response = requests.post(
            "http://localhost:8000/api/v1/packages/book",
            json=book_payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"成功: {result.get('success')}")
        print(f"拦截级别: {result.get('intercept_level')}")
        print(f"消息: {result.get('message')}")
    else:
        print("跳过：没有 MU 航班的套餐")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 燃油费突增测试完成 ===")
