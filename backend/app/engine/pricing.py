import numpy as np
import pandas as pd
from datetime import timedelta
from typing import List, Tuple, Dict, Any
from app.schemas import FlightInfo, HotelInfo, TimeWindow, PackageRecommendation


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
    candidates = []
    
    for flight in flights:
        for hotel in hotels:
            conflict_free, stay_days = check_time_conflict(flight, hotel, time_window)
            
            flight_discounted, flight_discount = calculate_flight_price(flight)
            hotel_discounted, hotel_discount, _ = calculate_hotel_total_price(hotel)
            
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
    
    df = pd.DataFrame(candidates)
    return df
