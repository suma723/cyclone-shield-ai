"""
Infrastructure Vulnerability Engine for CYCLONE-SHIELD AI
Evaluates vulnerability and operational status of Roads, Hospitals, and Shelters
with explicit explainability reasons ("WHY it is vulnerable").
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
from src.risk_engine import calculate_area_risk, get_risk_level, get_risk_color


def evaluate_roads(
    roads_geojson: dict,
    storm_surge_m: float,
    rainfall_mm: float,
    wind_speed_kmh: float
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    """
    Calculate flood risk, accessibility, and status for each road feature.
    Returns DataFrame and a lookup dict by road_id.
    """
    road_rows = []
    road_dict = {}

    for feature in roads_geojson.get("features", []):
        props = feature.get("properties", {})
        road_id = props.get("road_id", "R00")
        name = props.get("name", "Unnamed Road")
        elevation = float(props.get("elevation_m", 15.0))
        coastal_dist = float(props.get("coastal_distance_km", 2.0))
        importance = props.get("importance", "Standard Route")

        risk_metrics = calculate_area_risk(
            elevation_m=elevation,
            coastal_distance_km=coastal_dist,
            storm_surge_m=storm_surge_m,
            rainfall_mm=rainfall_mm,
            wind_speed_kmh=wind_speed_kmh
        )

        flood_risk = risk_metrics["overall_risk"]

        # Determine passability and operational status
        if flood_risk >= 75.0 or storm_surge_m >= (elevation + 0.5):
            status = "BLOCKED"
            status_desc = "Critical Inundation - Submerged by Storm Surge / Severe Waterlogging"
            is_passable = False
            accessibility_score = max(5, 100 - flood_risk)
        elif flood_risk >= 50.0:
            status = "WATERLOGGED"
            status_desc = "Partial Inundation - Slow Moving / High Clearance Vehicles Only"
            is_passable = True
            accessibility_score = 100 - flood_risk
        else:
            status = "PASSABLE"
            status_desc = "Clear & Operational - Safe Evacuation Corridor"
            is_passable = True
            accessibility_score = 100 - flood_risk

        # Generate explainable reasons
        reasons = []
        if elevation < 6.0:
            reasons.append(f"Low coastal elevation ({elevation}m) below storm surge zone")
        if coastal_dist < 0.5:
            reasons.append(f"Direct coastal exposure ({coastal_dist}km from coastline)")
        if rainfall_mm > 200:
            reasons.append(f"Heavy rainfall ({rainfall_mm}mm) overwhelming local drainage")
        if not reasons:
            reasons.append(f"Elevated terrain ({elevation}m) affords good natural drainage")

        road_info = {
            "road_id": road_id,
            "name": name,
            "importance": importance,
            "elevation_m": elevation,
            "coastal_distance_km": coastal_dist,
            "flood_risk": flood_risk,
            "accessibility_score": round(accessibility_score, 1),
            "status": status,
            "status_desc": status_desc,
            "is_passable": is_passable,
            "risk_level": risk_metrics["risk_level"],
            "color": risk_metrics["color"],
            "reasons": reasons,
            "coordinates": feature.get("geometry", {}).get("coordinates", []),
            "connects": props.get("connects", [])
        }

        road_rows.append(road_info)
        road_dict[road_id] = road_info

    return pd.DataFrame(road_rows), road_dict


def evaluate_hospitals(
    hospitals_df: pd.DataFrame,
    road_dict: Dict[str, Dict[str, Any]],
    storm_surge_m: float,
    rainfall_mm: float,
    wind_speed_kmh: float
) -> pd.DataFrame:
    """
    Evaluate hospital vulnerability based on site flood risk AND access road status.
    """
    results = []

    for _, row in hospitals_df.iterrows():
        h_id = row["hospital_id"]
        name = row["name"]
        elevation = float(row["elevation"])
        r1_id = str(row.get("primary_access_road", ""))
        r2_id = str(row.get("secondary_access_road", ""))

        # Approximate coastal distance from coordinates (Visakhapatnam coast ~ 83.33)
        lon = float(row["longitude"])
        approx_coastal_dist = max(0.2, abs(83.33 - lon) * 111.0 * 0.95)

        # Site flood risk
        site_risk = calculate_area_risk(
            elevation_m=elevation,
            coastal_distance_km=approx_coastal_dist,
            storm_surge_m=storm_surge_m,
            rainfall_mm=rainfall_mm,
            wind_speed_kmh=wind_speed_kmh
        )
        h_flood_risk = site_risk["overall_risk"]

        # Road accessibility calculation
        r1 = road_dict.get(r1_id, None)
        r2 = road_dict.get(r2_id, None)

        r1_acc = r1["accessibility_score"] if r1 else 80.0
        r2_acc = r2["accessibility_score"] if r2 else 70.0

        r1_passable = r1["is_passable"] if r1 else True
        r2_passable = r2["is_passable"] if r2 else True

        # Accessibility considers primary (65%) and secondary (35%)
        road_accessibility = round(0.65 * r1_acc + 0.35 * r2_acc, 1)

        # Overall Vulnerability combines flood risk and inaccessible roads
        # Vulnerability = 50% Site Flood Risk + 50% (100 - Road Accessibility)
        vulnerability_score = round(0.50 * h_flood_risk + 0.50 * (100.0 - road_accessibility), 1)
        vulnerability_score = min(100.0, max(0.0, vulnerability_score))

        vulnerability_level = get_risk_level(vulnerability_score)

        # Detailed explainable "WHY"
        reasons = []
        if h_flood_risk > 70:
            reasons.append(f"High site flood exposure (elevation {elevation}m vs surge {storm_surge_m}m)")
        elif h_flood_risk > 40:
            reasons.append(f"Moderate site waterlogging hazard (elevation {elevation}m)")
        else:
            reasons.append(f"Safe elevated facility site ({elevation}m)")

        if r1 and not r1_passable:
            reasons.append(f"Primary access corridor [{r1['name']}] is BLOCKED by surge/flood")
        elif r1 and r1["status"] == "WATERLOGGED":
            reasons.append(f"Primary access corridor [{r1['name']}] is WATERLOGGED")
        else:
            reasons.append("Primary access road remains operational")

        if r2 and not r2_passable:
            reasons.append(f"Secondary backup route [{r2['name']}] is also impaired")
        elif r2 and r2_passable:
            reasons.append(f"Secondary route [{r2['name']}] available for emergency transit")

        results.append({
            "hospital_id": h_id,
            "name": name,
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "capacity": row["capacity"],
            "importance": row["importance"],
            "elevation": elevation,
            "flood_risk": h_flood_risk,
            "road_accessibility": road_accessibility,
            "vulnerability_score": vulnerability_score,
            "vulnerability_level": vulnerability_level,
            "color": get_risk_color(vulnerability_level),
            "primary_road": r1["name"] if r1 else "N/A",
            "secondary_road": r2["name"] if r2 else "N/A",
            "is_accessible": (r1_passable or r2_passable),
            "reasons": reasons
        })

    return pd.DataFrame(results)


def evaluate_shelters(
    shelters_df: pd.DataFrame,
    road_dict: Dict[str, Dict[str, Any]],
    storm_surge_m: float,
    rainfall_mm: float,
    wind_speed_kmh: float
) -> pd.DataFrame:
    """
    Evaluate designated cyclone shelters for safety, road accessibility, and operational status.
    """
    results = []

    for _, row in shelters_df.iterrows():
        s_id = row["shelter_id"]
        name = row["name"]
        elevation = float(row["elevation"])
        coastal_dist = float(row["coastal_distance"])
        capacity = int(row["capacity"])
        access_road_id = str(row.get("access_road_id", ""))

        site_risk = calculate_area_risk(
            elevation_m=elevation,
            coastal_distance_km=coastal_dist,
            storm_surge_m=storm_surge_m,
            rainfall_mm=rainfall_mm,
            wind_speed_kmh=wind_speed_kmh
        )
        shelter_flood_risk = site_risk["overall_risk"]

        road = road_dict.get(access_road_id, None)
        road_acc = road["accessibility_score"] if road else 80.0
        road_passable = road["is_passable"] if road else True

        # Safety Score: high is safe (0 to 100)
        safety_score = round(100.0 - (0.60 * shelter_flood_risk + 0.40 * (100.0 - road_acc)), 1)
        safety_score = max(0.0, min(100.0, safety_score))

        # Recommendation Status
        if shelter_flood_risk > 60.0 or not road_passable or safety_score < 40.0:
            status = "NOT RECOMMENDED"
            color = "#dc3545" # Red
        elif safety_score < 70.0:
            status = "CAUTION"
            color = "#fd7e14" # Orange
        else:
            status = "RECOMMENDED"
            color = "#28a745" # Green

        reasons = []
        if shelter_flood_risk > 60.0:
            reasons.append(f"High flood risk at shelter site ({shelter_flood_risk}/100) due to low elevation ({elevation}m)")
        else:
            reasons.append(f"Safe high-ground elevation ({elevation}m, {coastal_dist}km from shore)")

        if road and not road_passable:
            reasons.append(f"Connecting access road [{road['name']}] is BLOCKED")
        elif road and road["status"] == "WATERLOGGED":
            reasons.append(f"Access road [{road['name']}] has high waterlogging risk")
        else:
            reasons.append("Approaching access roads are clear and secure")

        reasons.append(f"Safety features: {row.get('safety_features', 'Standard')}")

        results.append({
            "shelter_id": s_id,
            "name": name,
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "capacity": capacity,
            "elevation": elevation,
            "coastal_distance": coastal_dist,
            "shelter_flood_risk": shelter_flood_risk,
            "road_accessibility": road_acc,
            "safety_score": safety_score,
            "status": status,
            "color": color,
            "safety_features": row.get("safety_features", ""),
            "access_road": road["name"] if road else "N/A",
            "reasons": reasons
        })

    return pd.DataFrame(results)
