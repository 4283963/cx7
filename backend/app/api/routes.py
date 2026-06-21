from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas import (
    PackageRequest,
    PackageResponse,
    PackageRecommendation,
    BookingRequest,
    BookingResult,
    PriceInterceptLevel,
    FuelSurgeConfig
)
from app.engine.pricing import build_candidate_matrix, apply_fuel_surge, get_airline_code, calculate_flight_price, calculate_hotel_total_price
from app.engine.optimizer import (
    solve_multi_objective_packages,
    get_all_candidates_for_visualization
)
import os, json, urllib.request, traceback

DEBUG_SERVER_URL = os.environ.get("DEBUG_SERVER_URL", "http://127.0.0.1:7777/event")
DEBUG_SESSION_ID = os.environ.get("DEBUG_SESSION_ID", "matrix-index-error")

def _dbg_log(event_type: str, data: dict):
    try:
        payload = json.dumps({
            "sessionId": DEBUG_SESSION_ID,
            "eventType": event_type,
            "runId": "pre-fix",
            "data": data
        }).encode("utf-8")
        req = urllib.request.Request(DEBUG_SERVER_URL, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=0.5)
    except Exception:
        pass

router = APIRouter()


@router.post("/packages/recommend", response_model=PackageResponse)
async def recommend_packages(request: PackageRequest):
    try:
        _dbg_log("recommend:enter", {
            "flights_count": len(request.flights),
            "hotels_count": len(request.hotels),
            "fuel_surge_enabled": request.fuel_surge.enabled if request.fuel_surge else False,
            "fuel_surge_airline": request.fuel_surge.target_airline if request.fuel_surge else None
        })
        
        candidate_df = build_candidate_matrix(
            flights=request.flights,
            hotels=request.hotels,
            time_window=request.time_window,
            fuel_surge=request.fuel_surge
        )
        
        recommendations, total_candidates = solve_multi_objective_packages(
            candidate_df=candidate_df,
            top_n=request.top_n,
            price_weight=request.price_weight,
            discount_weight=request.discount_weight
        )
        
        surge_count = sum(1 for r in recommendations if r.fuel_surge_applied)
        
        return PackageResponse(
            success=True,
            total_candidates=total_candidates,
            top_packages=recommendations,
            message=f"成功计算出 {len(recommendations)} 个最优套餐" + (f"，其中 {surge_count} 个受燃油费影响" if surge_count > 0 else "")
        )
    except Exception as e:
        # region debug-point exception-recommend
        _dbg_log("exception:recommend", {
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "traceback": traceback.format_exc()
        })
        # endregion
        raise HTTPException(status_code=500, detail=f"计算出错: {str(e)}")


@router.post("/packages/visualization")
async def get_visualization_data(request: PackageRequest):
    try:
        _dbg_log("visualization:enter", {
            "flights_count": len(request.flights),
            "hotels_count": len(request.hotels),
            "fuel_surge_enabled": request.fuel_surge.enabled if request.fuel_surge else False,
            "fuel_surge_airline": request.fuel_surge.target_airline if request.fuel_surge else None
        })
        
        candidate_df = build_candidate_matrix(
            flights=request.flights,
            hotels=request.hotels,
            time_window=request.time_window,
            fuel_surge=request.fuel_surge
        )
        
        all_candidates = get_all_candidates_for_visualization(
            candidate_df=candidate_df,
            price_weight=request.price_weight,
            discount_weight=request.discount_weight
        )
        
        recommendations, total_candidates = solve_multi_objective_packages(
            candidate_df=candidate_df,
            top_n=request.top_n,
            price_weight=request.price_weight,
            discount_weight=request.discount_weight
        )
        
        top_package_ids = [pkg.package_id for pkg in recommendations]
        
        conflict_free_count = len(all_candidates)
        surge_count = sum(1 for c in all_candidates if c.get('fuel_surge_applied', False))
        
        return {
            "success": True,
            "total_candidates": total_candidates,
            "conflict_free_count": conflict_free_count,
            "all_candidates": all_candidates,
            "top_package_ids": top_package_ids,
            "top_packages": recommendations,
            "fuel_surge_applied_count": surge_count,
            "fuel_surge_target": request.fuel_surge.target_airline if request.fuel_surge and request.fuel_surge.enabled else None
        }
    except Exception as e:
        # region debug-point exception-recommend
        _dbg_log("exception:recommend", {
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "traceback": traceback.format_exc()
        })
        # endregion
        raise HTTPException(status_code=500, detail=f"计算出错: {str(e)}")


@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "推荐计算引擎运行正常"}


@router.post("/packages/sample")
async def get_sample_data():
    from datetime import date, timedelta
    from app.schemas import FlightInfo, HotelInfo, TimeWindow
    
    today = date.today()
    
    sample_flights = [
        FlightInfo(
            flight_no=f"CA{i+1}001",
            departure_city="北京",
            arrival_city="上海",
            departure_date=today + timedelta(days=i*2 + 1),
            base_price=800 + i * 100,
            discount_rate=0.1 + i * 0.05
        )
        for i in range(6)
    ]
    
    sample_hotels = []
    for i in range(5):
        check_in = today + timedelta(days=i + 1)
        check_out = check_in + timedelta(days=2 + i % 3)
        sample_hotels.append(HotelInfo(
            hotel_id=f"HTL{i+1:03d}",
            hotel_name=f"上海{i+1}星级酒店",
            city="上海",
            check_in_date=check_in,
            check_out_date=check_out,
            daily_price=500 + i * 100,
            discount_rate=0.05 + i * 0.03
        ))
    
    sample_time_window = TimeWindow(
        earliest_departure=today,
        latest_return=today + timedelta(days=15),
        min_stay_days=1,
        max_stay_days=7
    )
    
    return {
        "flights": sample_flights,
        "hotels": sample_hotels,
        "time_window": sample_time_window
    }


@router.post("/packages/book", response_model=BookingResult)
async def book_package(request: BookingRequest):
    try:
        _dbg_log("booking:enter", {
            "package_id": request.package_id,
            "quoted_price": request.quoted_price,
            "fuel_surge_enabled": request.fuel_surge.enabled if request.fuel_surge else False,
            "fuel_surge_airline": request.fuel_surge.target_airline if request.fuel_surge else None
        })
        
        airline_code = get_airline_code(request.flight.flight_no)
        
        surged_flight, fuel_applied, base_before = apply_fuel_surge(
            request.flight, 
            request.fuel_surge if request.fuel_surge and request.fuel_surge.apply_on_booking else None
        )
        
        flight_discounted, flight_discount = calculate_flight_price(
            surged_flight if fuel_applied else request.flight
        )
        hotel_discounted, hotel_discount, stay_days = calculate_hotel_total_price(request.hotel)
        
        final_price = flight_discounted + hotel_discounted
        original_price = request.quoted_price
        price_change = final_price - original_price
        price_change_rate = price_change / original_price if original_price > 0 else 0
        
        _dbg_log("booking:price_check", {
            "original_price": original_price,
            "final_price": final_price,
            "price_change": price_change,
            "price_change_rate": price_change_rate,
            "fuel_applied": fuel_applied,
            "airline_code": airline_code
        })
        
        if not fuel_applied:
            result = BookingResult(
                success=True,
                intercept_level=PriceInterceptLevel.NONE,
                original_price=original_price,
                final_price=final_price,
                price_change_amount=price_change,
                price_change_rate=price_change_rate,
                message="价格一致，预订成功",
                surge_triggered=False,
                affected_airline=None
            )
            _dbg_log("booking:success_none", {"message": "No price change"})
            return result
        
        if price_change_rate <= 0.05:
            result = BookingResult(
                success=True,
                intercept_level=PriceInterceptLevel.WARNING,
                original_price=original_price,
                final_price=final_price,
                price_change_amount=price_change,
                price_change_rate=price_change_rate,
                message=f"价格变动 {(price_change_rate * 100):.1f}%，在可接受范围内，已自动确认",
                surge_triggered=True,
                affected_airline=airline_code
            )
            _dbg_log("booking:success_warning", {"price_change_rate": price_change_rate})
            return result
        
        if price_change_rate <= 0.3:
            downgraded_alt = {
                "option": "alternative_flight",
                "description": "为您推荐其他航空公司的替代航班",
                "suggested_airlines": [code for code in ["MU", "CZ", "HU", "3U", "ZH"] if code != airline_code]
            }
            result = BookingResult(
                success=False,
                intercept_level=PriceInterceptLevel.DOWNGRADED,
                original_price=original_price,
                final_price=final_price,
                price_change_amount=price_change,
                price_change_rate=price_change_rate,
                message=f"⚠️ 价格变动拦截：{airline_code}航空因燃油费突涨，价格上涨 {(price_change_rate * 100):.1f}%。已为您启动交易降级流程，推荐替代方案。",
                downgraded_alternative=downgraded_alt,
                surge_triggered=True,
                affected_airline=airline_code
            )
            _dbg_log("booking:downgraded", {
                "price_change_rate": price_change_rate,
                "airline": airline_code
            })
            return result
        
        result = BookingResult(
            success=False,
            intercept_level=PriceInterceptLevel.BLOCKED,
            original_price=original_price,
            final_price=final_price,
            price_change_amount=price_change,
            price_change_rate=price_change_rate,
            message=f"🚫 交易已拦截：{airline_code}航空价格暴涨 {(price_change_rate * 100):.1f}%，超出系统容忍阈值。为保障您的权益，交易已自动取消。",
            surge_triggered=True,
            affected_airline=airline_code
        )
        _dbg_log("booking:blocked", {
            "price_change_rate": price_change_rate,
            "airline": airline_code
        })
        return result
        
    except Exception as e:
        _dbg_log("exception:booking", {
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "traceback": traceback.format_exc()
        })
        raise HTTPException(status_code=500, detail=f"预订处理出错: {str(e)}")
