import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("=" * 60)
print("后端 API 综合测试")
print("=" * 60)

# 1. 健康检查
print("\n1. 健康检查:")
resp = client.get("/")
print(f"  状态: {resp.status_code} - {resp.json()['message']}")

# 2. 获取示例数据
print("\n2. 获取示例数据:")
resp = client.post("/api/v1/packages/sample")
sample = resp.json()
print(f"  航班: {len(sample['flights'])} 个, 酒店: {len(sample['hotels'])} 个")
print(f"  示例航班: {sample['flights'][0]['flight_no']}")

# 3. 无燃油费的推荐
print("\n3. 推荐计算 (无燃油费):")
req_data = {
    "flights": sample["flights"][:4],
    "hotels": sample["hotels"][:3],
    "time_window": sample["time_window"],
    "top_n": 3,
    "price_weight": 0.5,
    "discount_weight": 0.5
}
resp = client.post("/api/v1/packages/visualization", json=req_data)
viz = resp.json()
print(f"  状态: {resp.status_code}, 成功: {viz['success']}")
print(f"  候选: {viz['total_candidates']} 总, {viz['conflict_free_count']} 无冲突")
print(f"  推荐 Top {len(viz['top_packages'])}:")
for p in viz['top_packages']:
    print(f"    #{p['rank']} {p['flight']['flight_no']}: ¥{p['discounted_total_price']:.0f} (surge={p.get('fuel_surge_applied', False)})")

# 4. 带燃油费的推荐
print("\n4. 推荐计算 (CA航空 +200% 燃油费):")
req_surge = {
    **req_data,
    "fuel_surge": {
        "enabled": True,
        "target_airline": "CA",
        "price_increase_rate": 2.0,
        "apply_on_booking": True
    }
}
resp = client.post("/api/v1/packages/visualization", json=req_surge)
viz_surge = resp.json()
print(f"  状态: {resp.status_code}")
print(f"  受燃油费影响: {viz_surge['fuel_surge_applied_count']} 个")
print(f"  目标航司: {viz_surge['fuel_surge_target']}")
print(f"  推荐列表:")
for p in viz_surge['top_packages']:
    print(f"    #{p['rank']} {p['flight']['flight_no']}: ¥{p['discounted_total_price']:.0f} (燃油费={p['fuel_surge_applied']})")

# 5. 预订拦截 - 受影响的航班
print("\n5. 预订测试 - 受燃油费影响的航班:")
surge_pkg = next((p for p in viz_surge['top_packages'] if p['fuel_surge_applied']), None)
if surge_pkg:
    book_req = {
        "package_id": surge_pkg['package_id'],
        "flight": surge_pkg['flight'],
        "hotel": surge_pkg['hotel'],
        "quoted_price": surge_pkg['discounted_total_price'],
        "fuel_surge": {
            "enabled": True,
            "target_airline": "CA",
            "price_increase_rate": 2.0,
            "apply_on_booking": True
        }
    }
    resp = client.post("/api/v1/packages/book", json=book_req)
    result = resp.json()
    print(f"  状态: {resp.status_code}")
    print(f"  拦截级别: {result['intercept_level']}")
    print(f"  成功: {result['success']}")
    print(f"  原价: ¥{result['original_price']:.0f}")
    print(f"  现价: ¥{result['final_price']:.0f}")
    print(f"  涨幅: {(result['price_change_rate']*100):.1f}%")
    print(f"  消息: {result['message'][:60]}...")
    if result.get('downgraded_alternative'):
        alt = result['downgraded_alternative']
        print(f"  降级方案: {alt['description']}")
        print(f"  推荐航司: {', '.join(alt['suggested_airlines'][:3])}")
else:
    print("  没有找到受燃油费影响的航班")

# 6. 预订 - 不受影响的航班
print("\n6. 预订测试 - 不受影响的航班:")
normal_pkg = next((p for p in viz_surge['top_packages'] if not p['fuel_surge_applied']), None)
if normal_pkg:
    book_req = {
        "package_id": normal_pkg['package_id'],
        "flight": normal_pkg['flight'],
        "hotel": normal_pkg['hotel'],
        "quoted_price": normal_pkg['discounted_total_price'],
        "fuel_surge": {
            "enabled": True,
            "target_airline": "CA",
            "price_increase_rate": 2.0,
            "apply_on_booking": True
        }
    }
    resp = client.post("/api/v1/packages/book", json=book_req)
    result = resp.json()
    print(f"  状态: {resp.status_code}")
    print(f"  拦截级别: {result['intercept_level']}")
    print(f"  成功: {result['success']}")
    print(f"  消息: {result['message']}")
else:
    print("  没有找到不受影响的航班")

print("\n" + "=" * 60)
print("所有测试完成!")
print("=" * 60)
