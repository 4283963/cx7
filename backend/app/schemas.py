from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from enum import Enum


class AirlineCode(str, Enum):
    CA = "CA"
    MU = "MU"
    CZ = "CZ"
    HU = "HU"
    SICHUAN = "3U"
    ZH = "ZH"


class FuelSurgeConfig(BaseModel):
    enabled: bool = False
    target_airline: str = "CA"
    price_increase_rate: float = Field(default=2.0, ge=0, le=10)
    apply_on_booking: bool = True


class PriceInterceptLevel(str, Enum):
    NONE = "none"
    WARNING = "warning"
    BLOCKED = "blocked"
    DOWNGRADED = "downgraded"


class BookingResult(BaseModel):
    success: bool
    intercept_level: PriceInterceptLevel
    original_price: float
    final_price: float
    price_change_amount: float
    price_change_rate: float
    message: str
    downgraded_alternative: Optional[dict] = None
    surge_triggered: bool = False
    affected_airline: Optional[str] = None


class FlightInfo(BaseModel):
    flight_no: str
    departure_city: str
    arrival_city: str
    departure_date: date
    base_price: float = Field(gt=0)
    discount_rate: float = Field(default=0.0, ge=0, le=1)
    
    @property
    def airline_code(self) -> str:
        if not self.flight_no:
            return ""
        for i, char in enumerate(self.flight_no):
            if char.isdigit():
                return self.flight_no[:i]
        return self.flight_no


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
    fuel_surge: Optional[FuelSurgeConfig] = None


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
    fuel_surge_applied: bool = False
    base_price_before_surge: Optional[float] = None


class BookingRequest(BaseModel):
    package_id: str
    flight: FlightInfo
    hotel: HotelInfo
    quoted_price: float
    fuel_surge: Optional[FuelSurgeConfig] = None


class PackageResponse(BaseModel):
    success: bool
    total_candidates: int
    top_packages: List[PackageRecommendation]
    message: Optional[str] = None
