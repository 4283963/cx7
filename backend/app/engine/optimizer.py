import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from app.schemas import PackageRecommendation, FlightInfo, HotelInfo
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


def normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    # region debug-point normalize_scores-enter
    _dbg_log("normalize_scores:enter", {
        "df_shape": list(df.shape),
        "df_empty": df.empty,
        "df_columns": df.columns.tolist()
    })
    # endregion
    
    if df.empty:
        _dbg_log("normalize_scores:empty_df", {"message": "DataFrame is empty, returning with norm columns"})
        df = df.copy()
        df['price_norm'] = pd.Series(dtype='float64')
        df['discount_norm'] = pd.Series(dtype='float64')
        return df
    
    REQUIRED_COLS = ['discounted_total_price', 'total_discount_rate']
    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing_cols:
        _dbg_log("normalize_scores:missing_cols", {"missing_cols": missing_cols})
        raise KeyError(f"Missing required columns for normalization: {missing_cols}")
    
    df = df.copy()
    
    price_min = df['discounted_total_price'].min()
    price_max = df['discounted_total_price'].max()
    
    if pd.isna(price_min) or pd.isna(price_max):
        _dbg_log("normalize_scores:price_nan", {"message": "Price min/max is NaN"})
        df['price_norm'] = 1.0
    elif price_max > price_min:
        df['price_norm'] = 1 - (df['discounted_total_price'] - price_min) / (price_max - price_min)
    else:
        df['price_norm'] = 1.0
    
    discount_min = df['total_discount_rate'].min()
    discount_max = df['total_discount_rate'].max()
    
    if pd.isna(discount_min) or pd.isna(discount_max):
        _dbg_log("normalize_scores:discount_nan", {"message": "Discount min/max is NaN"})
        df['discount_norm'] = 0.5
    elif discount_max > discount_min:
        df['discount_norm'] = (df['total_discount_rate'] - discount_min) / (discount_max - discount_min)
    else:
        df['discount_norm'] = 0.5
    
    df['price_norm'] = df['price_norm'].fillna(1.0)
    df['discount_norm'] = df['discount_norm'].fillna(0.5)
    
    # region debug-point normalize_scores-exit
    _dbg_log("normalize_scores:exit", {
        "has_price_norm": 'price_norm' in df.columns,
        "has_discount_norm": 'discount_norm' in df.columns,
        "price_norm_sample": df['price_norm'].iloc[0] if not df.empty else None,
        "discount_norm_sample": df['discount_norm'].iloc[0] if not df.empty else None
    })
    # endregion
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
    # region debug-point pareto_optimal_filter-enter
    _dbg_log("pareto_optimal_filter:enter", {
        "df_shape": list(df.shape),
        "df_empty": df.empty,
        "df_columns": df.columns.tolist()
    })
    # endregion
    if df.empty:
        df = df.copy()
        df['is_pareto_optimal'] = pd.Series(dtype='bool')
        return df
    
    REQUIRED_COLS = ['discounted_total_price', 'total_discount_rate']
    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing_cols:
        _dbg_log("pareto_optimal_filter:missing_cols", {"missing_cols": missing_cols})
        raise KeyError(f"Missing required columns for pareto filter: {missing_cols}")
    
    df = df.copy()
    prices = df['discounted_total_price'].values
    discounts = df['total_discount_rate'].values
    
    n = len(df)
    if len(prices) != n or len(discounts) != n:
        _dbg_log("pareto_optimal_filter:length_mismatch", {
            "len_df": n,
            "len_prices": len(prices),
            "len_discounts": len(discounts)
        })
        raise IndexError(f"Array length mismatch: df={n}, prices={len(prices)}, discounts={len(discounts)}")
    
    # region debug-point pareto_optimal_filter-arrays
    _dbg_log("pareto_optimal_filter:arrays", {
        "prices_len": len(prices),
        "discounts_len": len(discounts),
        "prices_type": str(type(prices)),
        "discounts_type": str(type(discounts)),
        "prices_sample": prices[:3].tolist() if len(prices) > 0 else [],
        "discounts_sample": discounts[:3].tolist() if len(discounts) > 0 else []
    })
    # endregion
    
    is_pareto = np.ones(n, dtype=bool)
    
    for i in range(n):
        if not is_pareto[i]:
            continue
        # region debug-point pareto_optimal_filter-loop-i
        _dbg_log("pareto_optimal_filter:loop_i", {
            "i": i,
            "len_df": n,
            "is_pareto_i": bool(is_pareto[i]),
            "prices_i": float(prices[i]),
            "discounts_i": float(discounts[i])
        })
        # endregion
        for j in range(n):
            if i == j or not is_pareto[j]:
                continue
            # region debug-point pareto_optimal_filter-loop-j
            _dbg_log("pareto_optimal_filter:loop_j", {
                "j": j,
                "prices_j": float(prices[j]),
                "discounts_j": float(discounts[j])
            })
            # endregion
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
    _dbg_log("solve_multi_objective:enter", {
        "df_shape": list(candidate_df.shape),
        "df_empty": candidate_df.empty,
        "df_columns": candidate_df.columns.tolist()
    })
    
    if candidate_df.empty:
        _dbg_log("solve_multi_objective:empty", {"message": "candidate_df is empty"})
        return [], 0
    
    REQUIRED_COLS = ['conflict_free', 'discounted_total_price', 'total_discount_rate',
                     'flight_obj', 'hotel_obj', 'original_total_price',
                     'total_discount_amount', 'stay_days', 'flight_no', 'hotel_id']
    missing_cols = [col for col in REQUIRED_COLS if col not in candidate_df.columns]
    if missing_cols:
        _dbg_log("solve_multi_objective:missing_cols", {"missing_cols": missing_cols})
        raise KeyError(f"Missing required columns: {missing_cols}")
    
    valid_df = candidate_df[candidate_df['conflict_free']].copy()
    total_candidates = len(valid_df)
    
    if total_candidates == 0:
        _dbg_log("solve_multi_objective:no_valid", {"message": "No conflict-free candidates"})
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
        
        fuel_applied = bool(row.get('fuel_surge_applied', False)) if 'fuel_surge_applied' in row else False
        base_before = float(row['base_price_before_surge']) if fuel_applied and 'base_price_before_surge' in row and pd.notna(row['base_price_before_surge']) else None
        
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
            conflict_free=row['conflict_free'],
            fuel_surge_applied=fuel_applied,
            base_price_before_surge=base_before
        )
        recommendations.append(pkg)
    
    return recommendations, total_candidates


def get_all_candidates_for_visualization(candidate_df: pd.DataFrame,
                                         price_weight: float = 0.5,
                                         discount_weight: float = 0.5) -> List[Dict[str, Any]]:
    _dbg_log("get_visualization:enter", {
        "df_shape": list(candidate_df.shape),
        "df_empty": candidate_df.empty,
        "df_columns": candidate_df.columns.tolist()
    })
    
    if candidate_df.empty:
        _dbg_log("get_visualization:empty", {"message": "candidate_df is empty"})
        return []
    
    REQUIRED_COLS = ['conflict_free', 'discounted_total_price', 'total_discount_rate',
                     'original_total_price', 'stay_days', 'flight_no', 'hotel_id']
    missing_cols = [col for col in REQUIRED_COLS if col not in candidate_df.columns]
    if missing_cols:
        _dbg_log("get_visualization:missing_cols", {"missing_cols": missing_cols})
        raise KeyError(f"Missing required columns: {missing_cols}")
    
    valid_df = candidate_df[candidate_df['conflict_free']].copy()
    if len(valid_df) == 0:
        _dbg_log("get_visualization:no_valid", {"message": "No conflict-free candidates"})
        return []
    
    valid_df = calculate_recommendation_score(valid_df, price_weight, discount_weight)
    valid_df = pareto_optimal_filter(valid_df)
    
    result = []
    for _, row in valid_df.iterrows():
        fuel_applied = bool(row.get('fuel_surge_applied', False)) if 'fuel_surge_applied' in row else False
        base_before = float(row['base_price_before_surge']) if fuel_applied and 'base_price_before_surge' in row and pd.notna(row['base_price_before_surge']) else None
        result.append({
            'package_id': f"{row['flight_no']}-{row['hotel_id']}",
            'discounted_total_price': round(row['discounted_total_price'], 2),
            'recommendation_score': round(row['recommendation_score'], 4),
            'total_discount_rate': round(row['total_discount_rate'], 4),
            'original_total_price': round(row['original_total_price'], 2),
            'is_pareto_optimal': bool(row['is_pareto_optimal']),
            'flight_no': row['flight_no'],
            'hotel_id': row['hotel_id'],
            'stay_days': int(row['stay_days']),
            'fuel_surge_applied': fuel_applied,
            'base_price_before_surge': base_before
        })
    
    return result
