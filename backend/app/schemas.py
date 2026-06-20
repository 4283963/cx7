from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class FlightInfo(BaseModel):
    flight_no: str
    departure_city: str
    arrival_city: str
    departure_date: date
    base_price: float = Field(gt=0)
    discount_rate: float = Field(default=0.0, ge=0, le=1)


class HotelInfo(BaseModel):
    hotel_id: str
    hotel_name: str
    city: str
    check_in_date: date
    check_out_date: date
    daily_price: float = Field(gt=0)
    discount_rate: float = Field(default=0.0, ge=0, le=1)


class TimeWindow(BaseModel):
    earliest_departure: date
    latest_return: date
    min_stay_days: int = Field(default=1, ge=1)
    max_stay_days: int = Field(default=14, ge=1)


class PackageRequest(BaseModel):
    flights: List[FlightInfo]
    hotels: List[HotelInfo]
    time_window: TimeWindow
    top_n: int = Field(default=5, ge=1, le=20)
    price_weight: float = Field(default=0.5, ge=0, le=1)
    discount_weight: float = Field(default=0.5, ge=0, le=1)


class PackageRecommendation(BaseModel):
    rank: int
    package_id: str
    flight: FlightInfo
    hotel: HotelInfo
    original_total_price: float
    discounted_total_price: float
    total_discount_amount: float
    total_discount_rate: float
    recommendation_score: float
    stay_days: int
    conflict_free: bool


class PackageResponse(BaseModel):
    success: bool
    total_candidates: int
    top_packages: List[PackageRecommendation]
    message: Optional[str] = None
