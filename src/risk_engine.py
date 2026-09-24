"""
Transparent Hazard & Risk Calculation Engine for CYCLONE-SHIELD AI
Implements the 4-component weighted model:
- 40% Elevation Risk
- 30% Storm Surge Exposure
- 20% Rainfall Risk
- 10% Coastal Proximity
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


SCENARIO_PRESETS = {
    "Low": {
        "storm_surge_m": 0.8,
        "rainfall_mm": 60.0,
        "wind_speed_kmh": 65,
        "description": "Depression / Deep Depression - minor tidal surge, manageable localized showers."
    },
    "Moderate": {
        "storm_surge_m": 1.8,
        "rainfall_mm": 160.0,
        "wind_speed_kmh": 105,
        "description": "Cyclonic Storm - moderate tidal surge, waterlogging in low-lying coastal pockets."
    },
    "Severe": {
        "storm_surge_m": 3.2,
        "rainfall_mm": 280.0,
        "wind_speed_kmh": 145,
        "description": "Very Severe Cyclonic Storm (VSCS - e.g. Hudhud benchmark) - severe surge, inundation of coastal arterials."
    },
    "Extreme": {
        "storm_surge_m": 5.0,
        "rainfall_mm": 420.0,
        "wind_speed_kmh": 195,
        "description": "Extremely Severe / Super Cyclone - catastrophic storm surge overtopping seawalls, heavy torrential flash floods."
    }
}


def get_risk_level(score: float) -> str:
    """Classify 0-100 risk score into standard disaster alert categories."""
    if score <= 30:
        return "LOW"
    elif score <= 60:
        return "MEDIUM"
    elif score <= 80:
        return "HIGH"
    else:
        return "CRITICAL"


def get_risk_color(level: str) -> str:
    """Return hex color corresponding to risk level."""
    mapping = {
        "LOW": "#28a745",      # Green
        "MEDIUM": "#ffc107",   # Yellow/Amber
        "HIGH": "#fd7e14",     # Orange
        "CRITICAL": "#dc3545"  # Red
    }
    return mapping.get(level, "#6c757d")


def calculate_area_risk(
    elevation_m: float,
    coastal_distance_km: float,
    storm_surge_m: float,
    rainfall_mm: float,
    wind_speed_kmh: float
) -> Dict[str, Any]:
    """
    Calculate explainable risk breakdown for a single geographic entity.
    Returns normalized 0-100 component scores and total weighted risk.
    """
    # 1. Elevation Risk (40% weight): Lower elevation = higher vulnerability
    # If surge exceeds elevation, inundation is direct
    buffer = elevation_m - storm_surge_m
    if buffer <= 0:
        elev_risk = min(100.0, 85.0 + abs(buffer) * 5.0)
    elif buffer < 4.0:
        elev_risk = 65.0 + (4.0 - buffer) * 5.0
    elif buffer < 15.0:
        elev_risk = 25.0 + ((15.0 - buffer) / 11.0) * 40.0
    else:
        # High ground > 15m above surge has minimal elevation risk
        elev_risk = max(5.0, 25.0 - ((buffer - 15.0) / 25.0) * 20.0)
    elev_risk = float(np.clip(elev_risk, 0.0, 100.0))

    # 2. Storm Surge Exposure (30% weight):
    # Surge height combined with coastal proximity decay (surge dissipates rapidly inland)
    surge_intensity = (storm_surge_m / 5.5) * 100.0
    surge_decay = max(0.0, 1.0 - (coastal_distance_km / 2.5))
    surge_risk = float(np.clip(surge_intensity * surge_decay * 1.15, 0.0, 100.0))

    # 3. Rainfall Risk (20% weight):
    # Base rainfall intensity combined with drainage slope difficulty
    rain_norm = (rainfall_mm / 450.0) * 100.0
    drainage_penalty = 1.15 if elevation_m < 8.0 else (0.85 if elevation_m > 20.0 else 1.0)
    rain_risk = float(np.clip(rain_norm * drainage_penalty, 0.0, 100.0))

    # 4. Coastal Proximity Risk (10% weight):
    # High within immediate 1.5km, decays beyond 3km
    proximity_risk = float(np.clip(100.0 - (coastal_distance_km / 3.0) * 90.0, 5.0, 100.0))

    # Calculate overall weighted score:
    # 40% Elevation + 30% Storm Surge + 20% Rainfall + 10% Coastal Proximity
    overall_score = (
        0.40 * elev_risk +
        0.30 * surge_risk +
        0.20 * rain_risk +
        0.10 * proximity_risk
    )
    overall_score = float(np.clip(round(overall_score, 1), 0.0, 100.0))
    risk_level = get_risk_level(overall_score)

    return {
        "elevation_risk": round(elev_risk, 1),
        "surge_risk": round(surge_risk, 1),
        "rainfall_risk": round(rain_risk, 1),
        "coastal_proximity_risk": round(proximity_risk, 1),
        "overall_risk": overall_score,
        "risk_level": risk_level,
        "color": get_risk_color(risk_level)
    }


def evaluate_all_areas(
    areas_df: pd.DataFrame,
    storm_surge_m: float,
    rainfall_mm: float,
    wind_speed_kmh: float
) -> pd.DataFrame:
    """Evaluate hazard and risk for all areas in dataframe."""
    results = []
    for _, row in areas_df.iterrows():
        metrics = calculate_area_risk(
            elevation_m=float(row["elevation"]),
            coastal_distance_km=float(row["coastal_distance"]),
            storm_surge_m=storm_surge_m,
            rainfall_mm=rainfall_mm,
            wind_speed_kmh=wind_speed_kmh
        )
        combined = {**row.to_dict(), **metrics}
        results.append(combined)

    return pd.DataFrame(results)
