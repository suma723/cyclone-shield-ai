"""
Interactive Map Utilities for CYCLONE-SHIELD AI
Builds multi-layered Folium maps for Visakhapatnam displaying:
- Risk-shaded community zones
- Road network with flood status & passability
- Critical healthcare facilities & vulnerability ratings
- Designated cyclone shelters with safety indicators
- Active safe evacuation corridors
"""

from typing import Dict, Any, List, Optional
import folium
from folium import plugins
import pandas as pd


def create_impact_map(
    areas_df: pd.DataFrame,
    roads_df: pd.DataFrame,
    hospitals_df: pd.DataFrame,
    shelters_df: pd.DataFrame,
    active_route: Optional[Dict[str, Any]] = None,
    selected_area_id: Optional[str] = None
) -> folium.Map:
    """
    Generate the primary interactive map for CYCLONE-SHIELD AI.
    Centered at Visakhapatnam: [17.725, 83.315], zoom 12.
    """
    m = folium.Map(
        location=[17.725, 83.315],
        zoom_start=12,
        tiles="CartoDB positron",
        control_scale=True
    )

    # Alternate Tile Layer (OpenStreetMap standard)
    folium.TileLayer("OpenStreetMap", name="Standard Street View").add_to(m)

    # Layer Groups for toggling in LayerControl
    fg_areas = folium.FeatureGroup(name="📍 Communities & Risk Zones", show=True)
    fg_roads = folium.FeatureGroup(name="🛣️ Road Network & Inundation", show=True)
    fg_hospitals = folium.FeatureGroup(name="🏥 Critical Hospitals", show=True)
    fg_shelters = folium.FeatureGroup(name="🛡️ Cyclone Shelters", show=True)
    fg_route = folium.FeatureGroup(name="🚀 Active Evacuation Route", show=True)

    # 1. Plot Areas (Community Risk Circles)
    for _, area in areas_df.iterrows():
        lat = float(area["latitude"])
        lon = float(area["longitude"])
        name = area["name"]
        risk = float(area.get("overall_risk", 20.0))
        level = area.get("risk_level", "LOW")
        color = area.get("color", "#28a745")
        elev = area.get("elevation", 10.0)
        pop = int(area.get("population", 10000))
        dist = area.get("coastal_distance", 1.0)
        is_selected = (selected_area_id == area["id"])

        popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-width: 200px; padding: 4px;">
            <h4 style="margin: 0 0 6px 0; color: #1e293b; border-bottom: 2px solid {color}; padding-bottom: 4px;">{name}</h4>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-size: 11px; background: {color}; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{level} RISK ({risk}/100)</span>
                <span style="font-size: 11px; color: #64748b;">Pop: {pop:,}</span>
            </div>
            <table style="width: 100%; font-size: 11px; color: #334155; line-height: 1.4;">
                <tr><td><b>Elevation:</b></td><td style="text-align: right;">{elev} m</td></tr>
                <tr><td><b>Coast Dist:</b></td><td style="text-align: right;">{dist} km</td></tr>
                <tr><td><b>Elevation Risk:</b></td><td style="text-align: right;">{area.get('elevation_risk', 'N/A')}</td></tr>
                <tr><td><b>Surge Risk:</b></td><td style="text-align: right;">{area.get('surge_risk', 'N/A')}</td></tr>
                <tr><td><b>Rainfall Risk:</b></td><td style="text-align: right;">{area.get('rainfall_risk', 'N/A')}</td></tr>
            </table>
        </div>
        """

        # Radius scaled by population & risk
        radius = 450 + (pop / 25000.0) * 250 + (risk / 100.0) * 200

        folium.Circle(
            location=[lat, lon],
            radius=radius,
            color=color,
            weight=3 if is_selected else 1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.35 if not is_selected else 0.65,
            tooltip=f"{name} — {level} Risk ({risk:.0f}/100)",
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(fg_areas)

    # 2. Plot Roads with Flood & Passability Status
    for _, road in roads_df.iterrows():
        coords = road.get("coordinates", [])
        if not coords:
            continue
        # Convert GeoJSON (lon, lat) to Folium (lat, lon)
        folium_coords = [[c[1], c[0]] for c in coords]
        status = road["status"]
        color = road["color"]
        name = road["name"]
        risk = road["flood_risk"]
        elev = road["elevation_m"]

        dash = "10, 8" if status == "BLOCKED" else ("6, 6" if status == "WATERLOGGED" else None)
        weight = 6 if status == "BLOCKED" else 4.5

        road_popup = f"""
        <div style="font-family: sans-serif; min-width: 190px;">
            <b style="color: #0f172a;">{name}</b><br/>
            <span style="font-size: 11px; background: {color}; color: white; padding: 1px 5px; border-radius: 3px;">
                {status} (Risk: {risk:.0f}/100)
            </span><br/>
            <small style="color: #475569;">Elevation: {elev}m | Coastal Dist: {road['coastal_distance_km']}km</small>
            <div style="margin-top: 4px; font-size: 11px; color: #1e293b;">
                <i>{road['status_desc']}</i>
            </div>
        </div>
        """

        folium.PolyLine(
            locations=folium_coords,
            color=color,
            weight=weight,
            opacity=0.85,
            dash_array=dash,
            tooltip=f"Road: {name} — {status}",
            popup=folium.Popup(road_popup, max_width=280)
        ).add_to(fg_roads)

    # 3. Plot Hospitals
    for _, hosp in hospitals_df.iterrows():
        lat = float(hosp["latitude"])
        lon = float(hosp["longitude"])
        name = hosp["name"]
        vuln = float(hosp["vulnerability_score"])
        level = hosp["vulnerability_level"]
        color = hosp["color"]

        icon_color = "red" if level in ["CRITICAL", "HIGH"] else "orange" if level == "MEDIUM" else "green"

        hosp_popup = f"""
        <div style="font-family: sans-serif; min-width: 220px;">
            <h4 style="margin: 0; color: #b91c1c;">🏥 {name}</h4>
            <div style="margin: 4px 0;">
                <span style="background: {color}; color: white; padding: 2px 5px; font-size: 10px; border-radius: 3px; font-weight: bold;">
                    Vulnerability: {vuln:.0f}/100 ({level})
                </span>
            </div>
            <table style="font-size: 11px; width: 100%;">
                <tr><td>Beds:</td><td><b>{hosp['capacity']}</b></td></tr>
                <tr><td>Site Flood Risk:</td><td><b>{hosp['flood_risk']:.0f}/100</b></td></tr>
                <tr><td>Road Accessibility:</td><td><b>{hosp['road_accessibility']:.0f}%</b></td></tr>
                <tr><td>Primary Corridor:</td><td>{hosp['primary_road']}</td></tr>
            </table>
            <div style="margin-top: 5px; font-size: 11px; color: #334155; border-top: 1px solid #cbd5e1; padding-top: 3px;">
                <b>Why Vulnerable:</b><br/>
                {'<br/>• '.join([''] + hosp['reasons'][:2])}
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            tooltip=f"Hospital: {name} — Vulnerability: {level}",
            popup=folium.Popup(hosp_popup, max_width=300),
            icon=folium.Icon(color=icon_color, icon="plus", prefix="fa")
        ).add_to(fg_hospitals)

    # 4. Plot Cyclone Shelters
    for _, shelter in shelters_df.iterrows():
        lat = float(shelter["latitude"])
        lon = float(shelter["longitude"])
        name = shelter["name"]
        status = shelter["status"]
        color = shelter["color"]
        icon_color = "green" if status == "RECOMMENDED" else ("orange" if status == "CAUTION" else "red")

        shelter_popup = f"""
        <div style="font-family: sans-serif; min-width: 220px;">
            <h4 style="margin: 0; color: #15803d;">🛡️ {name}</h4>
            <div style="margin: 4px 0;">
                <span style="background: {color}; color: white; padding: 2px 5px; font-size: 10px; border-radius: 3px; font-weight: bold;">
                    Status: {status}
                </span>
            </div>
            <table style="font-size: 11px; width: 100%;">
                <tr><td>Capacity:</td><td><b>{shelter['capacity']:,} persons</b></td></tr>
                <tr><td>Elevation:</td><td><b>{shelter['elevation']} m</b></td></tr>
                <tr><td>Site Flood Risk:</td><td><b>{shelter['shelter_flood_risk']:.0f}/100</b></td></tr>
                <tr><td>Access Road:</td><td>{shelter['access_road']}</td></tr>
            </table>
            <div style="font-size: 10px; color: #475569; margin-top: 4px;">
                <b>Features:</b> {shelter['safety_features']}
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            tooltip=f"Shelter: {name} — {status}",
            popup=folium.Popup(shelter_popup, max_width=300),
            icon=folium.Icon(color=icon_color, icon="home", prefix="fa")
        ).add_to(fg_shelters)

    # 5. Overlay Active Evacuation Route if available
    if active_route and "waypoints" in active_route and len(active_route["waypoints"]) >= 2:
        route_pts = active_route["waypoints"]
        folium.PolyLine(
            locations=route_pts,
            color="#2563eb",  # Bright Royal Blue
            weight=8,
            opacity=0.9,
            tooltip=f"Safe Corridor to {active_route.get('destination_name', 'Shelter')}",
            popup=f"Safe Evacuation Path ({active_route.get('total_distance_km')} km)"
        ).add_to(fg_route)

        # Pulse or start/end pinpoints
        folium.CircleMarker(
            location=route_pts[0],
            radius=9,
            color="#1d4ed8",
            fill=True,
            fill_color="#38bdf8",
            fill_opacity=1.0,
            tooltip="Route Origin (Evacuate from here)"
        ).add_to(fg_route)

        folium.Marker(
            location=route_pts[-1],
            tooltip=f"Safe Destination: {active_route.get('destination_name')}",
            icon=folium.Icon(color="blue", icon="flag-checkered", prefix="fa")
        ).add_to(fg_route)

    # Add all feature groups to map
    fg_areas.add_to(m)
    fg_roads.add_to(m)
    fg_hospitals.add_to(m)
    fg_shelters.add_to(m)
    fg_route.add_to(m)

    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    return m
