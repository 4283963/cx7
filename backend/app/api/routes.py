from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas import (
    PackageRequest,
    PackageResponse,
    PackageRecommendation
)
from app.engine.pricing import build_candidate_matrix
from app.engine.optimizer import (
    solve_multi_objective_packages,
    get_all_candidates_for_visualization
)

router = APIRouter()


@router.post("/packages/recommend", response_model=PackageResponse)
async def recommend_packages(request: PackageRequest):
    try:
        candidate_df = build_candidate_matrix(
            flights=request.flights,
            hotels=request.hotels,
            time_window=request.time_window
        )
        
        recommendations, total_candidates = solve_multi_objective_packages(
            candidate_df=candidate_df,
            top_n=request.top_n,
            price_weight=request.price_weight,
            discount_weight=request.discount_weight
        )
        
        return PackageResponse(
            success=True,
            total_candidates=total_candidates,
            top_packages=recommendations,
            message=f"成功计算出 {len(recommendations)} 个最优套餐"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算出错: {str(e)}")


@router.post("/packages/visualization")
async def get_visualization_data(request: PackageRequest):
    try:
        candidate_df = build_candidate_matrix(
            flights=request.flights,
            hotels=request.hotels,
            time_window=request.time_window
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
        
        return {
            "success": True,
            "total_candidates": total_candidates,
            "all_candidates": all_candidates,
            "top_package_ids": top_package_ids,
            "top_packages": recommendations
        }
    except Exception as e:
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
