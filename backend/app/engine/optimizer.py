import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from app.schemas import PackageRecommendation, FlightInfo, HotelInfo


def normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    price_min = df['discounted_total_price'].min()
    price_max = df['discounted_total_price'].max()
    if price_max > price_min:
        df['price_norm'] = 1 - (df['discounted_total_price'] - price_min) / (price_max - price_min)
    else:
        df['price_norm'] = 1.0
    
    discount_min = df['total_discount_rate'].min()
    discount_max = df['total_discount_rate'].max()
    if discount_max > discount_min:
        df['discount_norm'] = (df['total_discount_rate'] - discount_min) / (discount_max - discount_min)
    else:
        df['discount_norm'] = 0.5
    
    return df


def calculate_recommendation_score(df: pd.DataFrame, 
                                   price_weight: float = 0.5,
                                   discount_weight: float = 0.5) -> pd.DataFrame:
    df = df.copy()
    df = normalize_scores(df)
    
    total_weight = price_weight + discount_weight
    if total_weight == 0:
        price_weight = 0.5
        discount_weight = 0.5
        total_weight = 1.0
    
    df['recommendation_score'] = (
        price_weight * df['price_norm'] + 
        discount_weight * df['discount_norm']
    ) / total_weight
    
    return df


def pareto_optimal_filter(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    
    df = df.copy()
    prices = df['discounted_total_price'].values
    discounts = df['total_discount_rate'].values
    
    is_pareto = np.ones(len(df), dtype=bool)
    
    for i in range(len(df)):
        if not is_pareto[i]:
            continue
        for j in range(len(df)):
            if i == j or not is_pareto[j]:
                continue
            if (prices[j] <= prices[i] and discounts[j] >= discounts[i] and
                (prices[j] < prices[i] or discounts[j] > discounts[i])):
                is_pareto[i] = False
                break
    
    df['is_pareto_optimal'] = is_pareto
    return df


def solve_multi_objective_packages(candidate_df: pd.DataFrame,
                                    top_n: int = 5,
                                    price_weight: float = 0.5,
                                    discount_weight: float = 0.5) -> Tuple[List[PackageRecommendation], int]:
    if candidate_df.empty:
        return [], 0
    
    valid_df = candidate_df[candidate_df['conflict_free']].copy()
    total_candidates = len(valid_df)
    
    if total_candidates == 0:
        return [], 0
    
    valid_df = calculate_recommendation_score(valid_df, price_weight, discount_weight)
    valid_df = pareto_optimal_filter(valid_df)
    
    sorted_df = valid_df.sort_values(
        by=['recommendation_score', 'total_discount_rate'],
        ascending=[False, False]
    )
    
    top_df = sorted_df.head(top_n).reset_index(drop=True)
    
    recommendations = []
    for idx, row in top_df.iterrows():
        flight: FlightInfo = row['flight_obj']
        hotel: HotelInfo = row['hotel_obj']
        
        pkg = PackageRecommendation(
            rank=idx + 1,
            package_id=f"PKG-{idx + 1:03d}-{flight.flight_no}-{hotel.hotel_id}",
            flight=flight,
            hotel=hotel,
            original_total_price=round(row['original_total_price'], 2),
            discounted_total_price=round(row['discounted_total_price'], 2),
            total_discount_amount=round(row['total_discount_amount'], 2),
            total_discount_rate=round(row['total_discount_rate'], 4),
            recommendation_score=round(row['recommendation_score'], 4),
            stay_days=row['stay_days'],
            conflict_free=row['conflict_free']
        )
        recommendations.append(pkg)
    
    return recommendations, total_candidates


def get_all_candidates_for_visualization(candidate_df: pd.DataFrame,
                                         price_weight: float = 0.5,
                                         discount_weight: float = 0.5) -> List[Dict[str, Any]]:
    if candidate_df.empty:
        return []
    
    valid_df = candidate_df[candidate_df['conflict_free']].copy()
    if len(valid_df) == 0:
        return []
    
    valid_df = calculate_recommendation_score(valid_df, price_weight, discount_weight)
    valid_df = pareto_optimal_filter(valid_df)
    
    result = []
    for _, row in valid_df.iterrows():
        result.append({
            'package_id': f"{row['flight_no']}-{row['hotel_id']}",
            'discounted_total_price': round(row['discounted_total_price'], 2),
            'recommendation_score': round(row['recommendation_score'], 4),
            'total_discount_rate': round(row['total_discount_rate'], 4),
            'original_total_price': round(row['original_total_price'], 2),
            'is_pareto_optimal': bool(row['is_pareto_optimal']),
            'flight_no': row['flight_no'],
            'hotel_id': row['hotel_id'],
            'stay_days': int(row['stay_days'])
        })
    
    return result
