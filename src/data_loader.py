"""
Data Loader Module for CYCLONE-SHIELD AI
Loads local datasets for areas, hospitals, shelters, roads, and elevation.
Supports future Google Earth Engine (GEE) integration with seamless local fallback.
"""

import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_areas(data_mode: str = "Demo Data") -> pd.DataFrame:
    """Load geographic areas/localities around Visakhapatnam."""
    filepath = os.path.join(DATA_DIR, "areas.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        return df
    # Fallback default dataframe
    return pd.DataFrame([
        {"id": "A01", "name": "RK Beach Coastal Sector", "latitude": 17.7126, "longitude": 83.3180, "population": 18500, "elevation": 3.5, "coastal_distance": 0.15, "zone_type": "Coastal Lowland"},
        {"id": "A02", "name": "Lawson's Bay Colony", "latitude": 17.7289, "longitude": 83.3392, "population": 14200, "elevation": 4.0, "coastal_distance": 0.30, "zone_type": "Coastal Settlement"},
        {"id": "A03", "name": "Visakhapatnam Old Town / Port", "latitude": 17.6937, "longitude": 83.2985, "population": 26000, "elevation": 5.2, "coastal_distance": 0.40, "zone_type": "Dense Coastal Urban"},
        {"id": "A06", "name": "MVP Colony Sector 4", "latitude": 17.7391, "longitude": 83.3285, "population": 32000, "elevation": 12.0, "coastal_distance": 1.40, "zone_type": "Inland High Density"},
        {"id": "A07", "name": "Waltair Uplands", "latitude": 17.7202, "longitude": 83.3142, "population": 19500, "elevation": 28.0, "coastal_distance": 1.20, "zone_type": "Elevated Urban"}
    ])


def load_hospitals(data_mode: str = "Demo Data") -> pd.DataFrame:
    """Load hospitals in Visakhapatnam."""
    filepath = os.path.join(DATA_DIR, "hospitals.csv")
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return pd.DataFrame()


def load_shelters(data_mode: str = "Demo Data") -> pd.DataFrame:
    """Load designated cyclone shelters."""
    filepath = os.path.join(DATA_DIR, "shelters.csv")
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return pd.DataFrame()


def load_roads(data_mode: str = "Demo Data") -> dict:
    """Load road network as GeoJSON dict."""
    filepath = os.path.join(DATA_DIR, "roads.geojson")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}


def load_elevation_points(data_mode: str = "Demo Data") -> pd.DataFrame:
    """Load elevation grid points."""
    filepath = os.path.join(DATA_DIR, "elevation.csv")
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return pd.DataFrame()


def get_gee_status():
    """
    Check availability of Google Earth Engine authentication.
    Returns status tuple: (is_available: bool, message: str)
    """
    gee_project = os.getenv("GEE_PROJECT_ID")
    if not gee_project:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GEE_PROJECT_ID" in st.secrets:
                gee_project = str(st.secrets["GEE_PROJECT_ID"]).strip()
        except Exception:
            pass

    if gee_project:
        return True, f"GEE Configured (Project: {gee_project})"
    return False, "Demo Mode Active (Local High-Precision Visakhapatnam Data Layer)"
