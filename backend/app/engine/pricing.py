import numpy as np
import pandas as pd
from datetime import timedelta
from typing import List, Tuple, Dict, Any
from app.schemas import FlightInfo, HotelInfo, TimeWindow, PackageRecommendation
import os, json, urllib.request

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


def calculate_flight_price(flight: FlightInfo) -> Tuple[float, float]:
    discounted_price = flight.base_price * (1 - flight.discount_rate)
    discount_amount = flight.base_price - discounted_price
    return discounted_price, discount_amount


def calculate_hotel_total_price(hotel: HotelInfo) -> Tuple[float, float, int]:
    stay_days = (hotel.check_out_date - hotel.check_in_date).days
    if stay_days <= 0:
        stay_days = 1
    original_total = hotel.daily_price * stay_days
    discounted_total = original_total * (1 - hotel.discount_rate)
    discount_amount = original_total - discounted_total
    return discounted_total, discount_amount, stay_days


def check_time_conflict(flight: FlightInfo, hotel: HotelInfo, 
                        time_window: TimeWindow) -> Tuple[bool, int]:
    flight_date = flight.departure_date
    check_in = hotel.check_in_date
    check_out = hotel.check_out_date
    
    if flight_date < time_window.earliest_departure:
        return False, 0
    if check_out > time_window.latest_return:
        return False, 0
    
    stay_days = (check_out - check_in).days
    if stay_days < time_window.min_stay_days or stay_days > time_window.max_stay_days:
        return False, stay_days
    
    if flight_date < check_in:
        return False, stay_days
    if flight_date >= check_out:
        return False, stay_days
    
    return True, stay_days


def build_candidate_matrix(flights: List[FlightInfo], 
                           hotels: List[HotelInfo],
                           time_window: TimeWindow) -> pd.DataFrame:
    # region debug-point build_candidate_matrix-enter
    _dbg_log("build_candidate_matrix:enter", {
        "flights_count": len(flights),
        "hotels_count": len(hotels),
        "time_window": {
            "earliest": str(time_window.earliest_departure),
            "latest": str(time_window.latest_return),
            "min_days": time_window.min_stay_days,
            "max_days": time_window.max_stay_days
        }
    })
    # endregion
    candidates = []
    
    for flight in flights:
        for hotel in hotels:
            # region debug-point check_time_conflict-before
            _dbg_log("check_time_conflict:before", {
                "flight_no": flight.flight_no,
                "flight_date": str(flight.departure_date),
                "hotel_id": hotel.hotel_id,
                "check_in": str(hotel.check_in_date),
                "check_out": str(hotel.check_out_date)
            })
            # endregion
            conflict_free, stay_days = check_time_conflict(flight, hotel, time_window)
            # region debug-point check_time_conflict-after
            _dbg_log("check_time_conflict:after", {
                "conflict_free": conflict_free,
                "stay_days": stay_days
            })
            # endregion
            
            flight_discounted, flight_discount = calculate_flight_price(flight)
            hotel_discounted, hotel_discount, _ = calculate_hotel_total_price(hotel)
            
            # region debug-point price-calculation
            _dbg_log("price_calc:before_original_total", {
                "flight_base": flight.base_price,
                "hotel_daily": hotel.daily_price,
                "stay_days": stay_days,
                "max_stay_days_1": max(stay_days, 1)
            })
            # endregion
            original_total = flight.base_price + hotel.daily_price * max(stay_days, 1)
            discounted_total = flight_discounted + hotel_discounted
            total_discount_amount = original_total - discounted_total
            total_discount_rate = total_discount_amount / original_total if original_total > 0 else 0
            
            candidates.append({
                'flight_no': flight.flight_no,
                'hotel_id': hotel.hotel_id,
                'flight_departure_date': flight.departure_date,
                'hotel_check_in': hotel.check_in_date,
                'hotel_check_out': hotel.check_out_date,
                'stay_days': stay_days,
                'original_total_price': original_total,
                'discounted_total_price': discounted_total,
                'total_discount_amount': total_discount_amount,
                'total_discount_rate': total_discount_rate,
                'flight_discount_rate': flight.discount_rate,
                'hotel_discount_rate': hotel.discount_rate,
                'conflict_free': conflict_free,
                'flight_obj': flight,
                'hotel_obj': hotel
            })
    
    # region debug-point build_candidate_matrix-exit
    df = pd.DataFrame(candidates)
    
    REQUIRED_COLUMNS = [
        'flight_no', 'hotel_id', 'flight_departure_date', 'hotel_check_in',
        'hotel_check_out', 'stay_days', 'original_total_price',
        'discounted_total_price', 'total_discount_amount', 'total_discount_rate',
        'flight_discount_rate', 'hotel_discount_rate', 'conflict_free',
        'flight_obj', 'hotel_obj'
    ]
    
    if df.empty:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        for col in missing_cols:
            df[col] = None
    
    _dbg_log("build_candidate_matrix:exit", {
        "df_shape": list(df.shape),
        "df_columns": df.columns.tolist(),
        "df_empty": df.empty,
        "candidates_count": len(candidates),
        "missing_cols_filled": missing_cols
    })
    return df
    # endregion
