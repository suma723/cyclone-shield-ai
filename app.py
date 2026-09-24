"""
CYCLONE-SHIELD AI
AI-Powered Cyclone Impact, Infrastructure Vulnerability & Safe Evacuation Planner
Primary Study Area: Visakhapatnam, Andhra Pradesh, India

Author: Lead Full-Stack AI & Geospatial Developer
"""

import os
import json
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

# Streamlit Page Configuration
st.set_page_config(
    page_title="CYCLONE-SHIELD AI | Visakhapatnam Emergency Planner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import internal modular engines
from src.data_loader import (
    load_areas,
    load_hospitals,
    load_shelters,
    load_roads,
    load_elevation_points,
    get_gee_status
)
from src.risk_engine import SCENARIO_PRESETS, evaluate_all_areas, get_risk_level, get_risk_color
from src.infrastructure import evaluate_roads, evaluate_hospitals, evaluate_shelters
from src.cascade import analyze_cascade_impacts
from src.evacuation import recommend_shelters_for_area, calculate_safe_route
from src.gemini_advisor import generate_copilot_advisory, get_gemini_api_key
from src.alerts import SUPPORTED_LANGUAGES, build_multilingual_messages, generate_tts_audio
from utils.map_utils import create_impact_map
from utils.helpers import get_custom_css, render_kpi, render_phone_simulation
from streamlit_folium import st_folium

# Inject Custom Styling
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize Session State
if "has_run_analysis" not in st.session_state:
    st.session_state.has_run_analysis = True  # Auto-run initial baseline for immediate demo readiness
if "selected_scenario" not in st.session_state:
    st.session_state.selected_scenario = "Severe"
if "storm_surge_m" not in st.session_state:
    st.session_state.storm_surge_m = 3.2
if "rainfall_mm" not in st.session_state:
    st.session_state.rainfall_mm = 280.0
if "wind_speed_kmh" not in st.session_state:
    st.session_state.wind_speed_kmh = 145
if "selected_area_id" not in st.session_state:
    st.session_state.selected_area_id = "A01"  # Default: RK Beach Coastal Sector
if "selected_language" not in st.session_state:
    st.session_state.selected_language = "Telugu (తెలుగు)"
if "ai_advisory" not in st.session_state:
    st.session_state.ai_advisory = None
if "active_route" not in st.session_state:
    st.session_state.active_route = None

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo", "logo.svg")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span style="font-size: 2rem;">🛡️</span>
            <div>
                <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800; color: #0f172a; line-height: 1.2;">CYCLONE-SHIELD</h2>
                <span style="font-size: 0.75rem; color: #dc2626; font-weight: 700; letter-spacing: 0.5px;">DISASTER COPILOT AI</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.caption("AI-Powered Cyclone Impact & Safe Evacuation Planner")
    st.markdown("---")

    # Data Source & Study Area
    st.markdown("##### 📍 Target Jurisdiction")
    st.selectbox(
        "Study Area",
        ["Visakhapatnam, Andhra Pradesh, India"],
        index=0,
        disabled=True
    )

    gee_avail, gee_msg = get_gee_status()
    data_source_mode = st.radio(
        "Data Layer Architecture",
        ["Demo Data (Bundled High-Res Grid)", "Google Earth Engine (GEE Feed)"],
        index=0,
        help="CYCLONE-SHIELD AI runs 100% offline out-of-the-box with bundled high-precision geospatial sample data, and is architected to seamlessly plug into GEE."
    )
    if data_source_mode.startswith("Google"):
        if gee_avail:
            st.success(gee_msg)
        else:
            st.info("ℹ️ " + gee_msg + " (Automatic Local Fallback Active)")

    st.markdown("---")
    st.markdown("##### 🌀 Step 1 — Cyclone Scenario")

    preset_name = st.selectbox(
        "Scenario Preset",
        list(SCENARIO_PRESETS.keys()),
        index=list(SCENARIO_PRESETS.keys()).index(st.session_state.selected_scenario)
    )

    # Preset update trigger
    if preset_name != st.session_state.selected_scenario:
        st.session_state.selected_scenario = preset_name
        st.session_state.storm_surge_m = SCENARIO_PRESETS[preset_name]["storm_surge_m"]
        st.session_state.rainfall_mm = SCENARIO_PRESETS[preset_name]["rainfall_mm"]
        st.session_state.wind_speed_kmh = SCENARIO_PRESETS[preset_name]["wind_speed_kmh"]

    st.info(SCENARIO_PRESETS[preset_name]["description"])

    # Manual Fine-Tuning Sliders
    st.markdown("###### Parameter Fine-Tuning")
    storm_surge_val = st.slider(
        "Storm Surge Height (m)",
        min_value=0.0,
        max_value=6.0,
        value=float(st.session_state.storm_surge_m),
        step=0.2,
        help="Peak astronomical tide + cyclone storm surge height above mean sea level."
    )
    st.session_state.storm_surge_m = storm_surge_val

    rainfall_val = st.slider(
        "24h Rainfall Intensity (mm)",
        min_value=10.0,
        max_value=500.0,
        value=float(st.session_state.rainfall_mm),
        step=10.0,
        help="Anticipated 24-hour precipitation accumulation."
    )
    st.session_state.rainfall_mm = rainfall_val

    wind_val = st.slider(
        "Sustained Wind Speed (km/h)",
        min_value=40,
        max_value=220,
        value=int(st.session_state.wind_speed_kmh),
        step=5,
        help="Maximum sustained surface wind speeds."
    )
    st.session_state.wind_speed_kmh = wind_val

    st.markdown("---")
    st.markdown("##### 🌐 Alert Language")
    lang_choice = st.selectbox(
        "Default Alert Language",
        list(SUPPORTED_LANGUAGES.keys()),
        index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.selected_language)
    )
    st.session_state.selected_language = lang_choice

    st.markdown("---")
    run_btn = st.button("⚡ RUN IMPACT ANALYSIS", type="primary", use_container_width=True)
    if run_btn:
        st.session_state.has_run_analysis = True
        st.session_state.ai_advisory = None  # Reset advisory for new run
        st.session_state.active_route = None

    st.markdown("""
    <div style="font-size: 0.74rem; color: #475569; margin-top: 15px; border-top: 1px solid #e2e8f0; padding-top: 10px; background: #f8fafc; border-radius: 6px; padding: 10px;">
        <b style="color: #0f172a;">ℹ️ About / Demo Disclaimer:</b><br/>
        This is a prototype decision-support system for demonstration purposes. Risk values and recommendations are simulated/model-generated and are not official emergency warnings.
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# DATA INGESTION & PIPELINE COMPUTATION
# ==========================================
raw_areas = load_areas()
raw_hospitals = load_hospitals()
raw_shelters = load_shelters()
raw_roads = load_roads()
raw_elevation = load_elevation_points()

# Run Risk Engine Calculations
areas_evaluated = evaluate_all_areas(
    areas_df=raw_areas,
    storm_surge_m=st.session_state.storm_surge_m,
    rainfall_mm=st.session_state.rainfall_mm,
    wind_speed_kmh=st.session_state.wind_speed_kmh
)

roads_evaluated, road_dict = evaluate_roads(
    roads_geojson=raw_roads,
    storm_surge_m=st.session_state.storm_surge_m,
    rainfall_mm=st.session_state.rainfall_mm,
    wind_speed_kmh=st.session_state.wind_speed_kmh
)

hospitals_evaluated = evaluate_hospitals(
    hospitals_df=raw_hospitals,
    road_dict=road_dict,
    storm_surge_m=st.session_state.storm_surge_m,
    rainfall_mm=st.session_state.rainfall_mm,
    wind_speed_kmh=st.session_state.wind_speed_kmh
)

shelters_evaluated = evaluate_shelters(
    shelters_df=raw_shelters,
    road_dict=road_dict,
    storm_surge_m=st.session_state.storm_surge_m,
    rainfall_mm=st.session_state.rainfall_mm,
    wind_speed_kmh=st.session_state.wind_speed_kmh
)

cascade_alerts = analyze_cascade_impacts(
    areas_df=areas_evaluated,
    hospitals_df=hospitals_evaluated,
    shelters_df=shelters_evaluated,
    road_dict=road_dict
)

# Auto-compute initial active evacuation route if none selected
if st.session_state.active_route is None or st.session_state.active_route.get("origin_id") != st.session_state.selected_area_id:
    current_area_series = areas_evaluated[areas_evaluated["id"] == st.session_state.selected_area_id].iloc[0]
    initial_recs = recommend_shelters_for_area(current_area_series, shelters_evaluated, road_dict)
    if initial_recs:
        st.session_state.active_route = calculate_safe_route(
            area_id=st.session_state.selected_area_id,
            target_shelter_id=initial_recs[0]["shelter_id"],
            areas_df=areas_evaluated,
            shelters_df=shelters_evaluated,
            road_dict=road_dict
        )


# ==========================================
# MAIN INTERFACE HEADER & DEMO MODE INDICATOR
# ==========================================
active_api_key = get_gemini_api_key()
is_live_api = bool(active_api_key)

demo_badge_html = (
    '<span class="badge-live-gov" style="background: #16a34a; margin-left: 8px;">⚡ LIVE API MODE (Gemini Connected)</span>'
    if is_live_api
    else '<span class="badge-live-gov" style="background: #0284c7; margin-left: 8px;">🟢 DEMO MODE (Offline Grounded Engine Active)</span>'
)

st.markdown(f"""
<div class="disaster-header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
        <div>
            <h1>
                CYCLONE-SHIELD AI
                <span class="badge-live-gov">PROTOTYPE SITUATION ROOM</span>
                {demo_badge_html}
            </h1>
            <p>AI-Powered Cyclone Impact, Infrastructure Vulnerability & Safe Evacuation Planner</p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.8rem; color: #cbd5e1;">Target Area: <b>Visakhapatnam Metropolitan Region</b></div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Hazard Engine: 40% Elev • 30% Surge • 20% Rain • 10% Coast Dist</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# KPI METRIC CARDS (DYNAMIC DISASTER STATS)
# ==========================================
# Compute overall statistics
high_risk_areas = areas_evaluated[areas_evaluated["overall_risk"] >= 61.0]
exposed_population = int(high_risk_areas["population"].sum()) if not high_risk_areas.empty else 0
critical_hospitals = int((hospitals_evaluated["vulnerability_level"] == "CRITICAL").sum())
safe_shelters_count = int((shelters_evaluated["status"] == "RECOMMENDED").sum())
total_shelters_count = len(shelters_evaluated)
blocked_roads_count = int((roads_evaluated["status"] == "BLOCKED").sum())

max_risk_score = float(areas_evaluated["overall_risk"].max()) if not areas_evaluated.empty else 0.0
overall_risk_label = get_risk_level(max_risk_score)
overall_risk_color = get_risk_color(overall_risk_label)

kpi_cols = st.columns(5)
with kpi_cols[0]:
    st.markdown(render_kpi("Overall Risk", overall_risk_label, f"Max Score: {max_risk_score:.0f}/100", overall_risk_color), unsafe_allow_html=True)
with kpi_cols[1]:
    st.markdown(render_kpi("Population Exposed", f"{exposed_population:,}", "In High/Critical Flood Zones", "#e11d48"), unsafe_allow_html=True)
with kpi_cols[2]:
    st.markdown(render_kpi("Critical Hospitals", f"{critical_hospitals} / {len(hospitals_evaluated)}", "Access/Site Compromised", "#dc3545"), unsafe_allow_html=True)
with kpi_cols[3]:
    st.markdown(render_kpi("Safe Shelters", f"{safe_shelters_count} / {total_shelters_count}", "Operational High-Ground", "#16a34a"), unsafe_allow_html=True)
with kpi_cols[4]:
    st.markdown(render_kpi("Roads at Risk", f"{blocked_roads_count} Blocked", f"{len(roads_evaluated)} Arterials Tracked", "#ea580c"), unsafe_allow_html=True)

st.write("")


# ==========================================
# INTERACTIVE MAP SECTION
# ==========================================
st.markdown("### 🗺️ Geospatial Hazard & Infrastructure Map")

# Map container
map_col, info_col = st.columns([3, 1])

with info_col:
    st.markdown("##### 📍 Focus Community")
    area_options = {row["name"]: row["id"] for _, row in areas_evaluated.iterrows()}
    # Find current index
    current_area_name = areas_evaluated.loc[areas_evaluated["id"] == st.session_state.selected_area_id, "name"].values[0] if st.session_state.selected_area_id in areas_evaluated["id"].values else list(area_options.keys())[0]
    
    selected_name = st.selectbox(
        "Select Area to Inspect:",
        list(area_options.keys()),
        index=list(area_options.keys()).index(current_area_name),
        key="focus_community_select"
    )
    
    # Reactively update selected area and recompute route if changed
    if area_options[selected_name] != st.session_state.selected_area_id:
        st.session_state.selected_area_id = area_options[selected_name]
        sel_area_tmp = areas_evaluated[areas_evaluated["id"] == st.session_state.selected_area_id].iloc[0]
        recs_tmp = recommend_shelters_for_area(sel_area_tmp, shelters_evaluated, road_dict)
        if recs_tmp:
            st.session_state.active_route = calculate_safe_route(
                area_id=st.session_state.selected_area_id,
                target_shelter_id=recs_tmp[0]["shelter_id"],
                areas_df=areas_evaluated,
                shelters_df=shelters_evaluated,
                road_dict=road_dict
            )
        st.session_state.ai_advisory = None
        st.rerun()

    # Show selected area details
    sel_area_data = areas_evaluated[areas_evaluated["id"] == st.session_state.selected_area_id].iloc[0]
    
    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #0f172a;">{sel_area_data['name']}</b>
            <span style="background: {sel_area_data['color']}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: bold;">
                {sel_area_data['risk_level']}
            </span>
        </div>
        <div style="font-size: 1.4rem; font-weight: 800; color: {sel_area_data['color']}; margin: 4px 0;">
            {sel_area_data['overall_risk']:.0f} <span style="font-size: 0.8rem; color: #64748b;">/ 100 Risk</span>
        </div>
        <hr style="margin: 6px 0; border: none; border-top: 1px solid #e2e8f0;" />
        <div style="font-size: 0.8rem; color: #334155; line-height: 1.5;">
            <b>Population:</b> {int(sel_area_data['population']):,}<br/>
            <b>Elevation:</b> {sel_area_data['elevation']} m<br/>
            <b>Coast Distance:</b> {sel_area_data['coastal_distance']} km<br/>
            <b>Zone:</b> {sel_area_data['zone_type']}
        </div>
        <div style="margin-top: 8px; padding-top: 6px; border-top: 1px dashed #cbd5e1; font-size: 0.76rem; color: #475569;">
            <b>Formula Breakdown:</b><br/>
            • Elevation (40%): {sel_area_data['elevation_risk']:.0f}<br/>
            • Surge Exp (30%): {sel_area_data['surge_risk']:.0f}<br/>
            • Rainfall (20%): {sel_area_data['rainfall_risk']:.0f}<br/>
            • Proximity (10%): {sel_area_data['coastal_proximity_risk']:.0f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick action to find shelter
    if st.button("🧭 Re-Calculate Safe Shelter & Route", use_container_width=True, type="secondary"):
        shelter_recs = recommend_shelters_for_area(sel_area_data, shelters_evaluated, road_dict)
        top_shelter = shelter_recs[0]
        st.session_state.active_route = calculate_safe_route(
            area_id=st.session_state.selected_area_id,
            target_shelter_id=top_shelter["shelter_id"],
            areas_df=areas_evaluated,
            shelters_df=shelters_evaluated,
            road_dict=road_dict
        )
        st.toast(f"Optimal safe route calculated to {top_shelter['name']}!", icon="🛡️")
        st.rerun()

with map_col:
    # Render Folium Map
    folium_map = create_impact_map(
        areas_df=areas_evaluated,
        roads_df=roads_evaluated,
        hospitals_df=hospitals_evaluated,
        shelters_df=shelters_evaluated,
        active_route=st.session_state.active_route,
        selected_area_id=st.session_state.selected_area_id
    )
    st_folium(folium_map, width="100%", height=500, returned_objects=[])

    st.markdown("""
    <div style="display: flex; gap: 16px; font-size: 0.76rem; color: #475569; margin-top: 6px; flex-wrap: wrap;">
        <span>🟢 <b>Low Risk (0-30)</b></span>
        <span>🟡 <b>Medium Risk (31-60)</b></span>
        <span>🟠 <b>High Risk (61-80)</b></span>
        <span>🔴 <b>Critical Risk (81-100)</b></span>
        <span>| &nbsp; <b>Dashed Roads:</b> Submerged/Inundated</span>
        <span>| &nbsp; <b>Solid Blue Line:</b> Safe Evacuation Corridor</span>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# ==========================================
# TABBED DEEP-DIVE SECTIONS
# ==========================================
tabs = st.tabs([
    "🏥 Infrastructure Vulnerability",
    "⚡ Cascade Impact Analysis",
    "🛡️ Safe Shelter & Evacuation Routing",
    "🤖 Gemini AI Disaster Copilot",
    "📱 Multilingual Alert & Mobile Simulation"
])


# ------------------------------------------
# TAB 1: INFRASTRUCTURE VULNERABILITY
# ------------------------------------------
with tabs[0]:
    st.markdown("### 🏥 Infrastructure Vulnerability Breakdown")
    st.caption("Site flood vulnerability combined with approaching corridor accessibility.")

    infra_subtabs = st.tabs([
        "Hospitals Vulnerability",
        "Road Passability & Flood Risk",
        "Cyclone Shelters Status",
        "Digital Elevation Sampling Grid"
    ])

    with infra_subtabs[0]:
        st.markdown("#### Healthcare Infrastructure Accessibility")
        hosp_cols = st.columns(2)
        for idx, (_, hosp) in enumerate(hospitals_evaluated.iterrows()):
            with hosp_cols[idx % 2]:
                st.markdown(f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {hosp['color']}; border-radius: 8px; padding: 12px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #0f172a; font-size: 1rem;">🏥 {hosp['name']}</h4>
                        <span style="background: {hosp['color']}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                            {hosp['vulnerability_level']} ({hosp['vulnerability_score']:.0f}/100)
                        </span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748b; margin: 4px 0 8px 0;">
                        {hosp['importance']} • Capacity: <b>{hosp['capacity']} beds</b> • Elevation: <b>{hosp['elevation']}m</b>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem; background: #f8fafc; padding: 8px; border-radius: 6px;">
                        <div><b>Site Flood Risk:</b> {hosp['flood_risk']:.0f}/100</div>
                        <div><b>Road Accessibility:</b> {hosp['road_accessibility']:.0f}%</div>
                        <div><b>Primary Road:</b> {hosp['primary_road']}</div>
                        <div><b>Secondary Road:</b> {hosp['secondary_road']}</div>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.78rem; color: #334155;">
                        <b>Explainable Vulnerability Rationale:</b>
                        <ul style="margin: 2px 0 0 0; padding-left: 18px;">
                            {''.join([f'<li>{r}</li>' for r in hosp['reasons']])}
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with infra_subtabs[1]:
        st.markdown("#### Strategic Road Network Operational Status")
        road_table_data = []
        for _, r in roads_evaluated.iterrows():
            road_table_data.append({
                "Road ID": r["road_id"],
                "Corridor Name": r["name"],
                "Elevation (m)": r["elevation_m"],
                "Flood Risk (0-100)": f"{r['flood_risk']:.0f}",
                "Status": r["status"],
                "Accessibility Score": f"{r['accessibility_score']:.0f}%",
                "Traffic Action": r["status_desc"]
            })
        st.dataframe(pd.DataFrame(road_table_data), use_container_width=True, hide_index=True)

    with infra_subtabs[2]:
        st.markdown("#### Designated Cyclone Shelters Suitability")
        shelter_table = []
        for _, s in shelters_evaluated.iterrows():
            shelter_table.append({
                "Shelter ID": s["shelter_id"],
                "Shelter Name": s["name"],
                "Elevation (m)": s["elevation"],
                "Capacity (Persons)": f"{s['capacity']:,}",
                "Site Flood Risk": f"{s['shelter_flood_risk']:.0f}/100",
                "Safety Score": f"{s['safety_score']:.0f}/100",
                "Recommendation Status": s["status"],
                "Access Road": s["access_road"]
            })
        st.dataframe(pd.DataFrame(shelter_table), use_container_width=True, hide_index=True)

    with infra_subtabs[3]:
        st.markdown("#### Digital Elevation Topography Grid (Visakhapatnam)")
        st.caption("Empirical elevation sampling points used by the risk engine to calibrate flood buffers.")
        if not raw_elevation.empty:
            st.dataframe(raw_elevation, use_container_width=True, hide_index=True)
        else:
            st.info("Elevation sampling dataset is empty.")


# ------------------------------------------
# TAB 2: CASCADE IMPACT ANALYSIS
# ------------------------------------------
with tabs[1]:
    st.markdown("### ⚡ Cascade Dependency & Infrastructure Impact Analysis")
    st.caption("Reveals domino-effect failures across transportation links, healthcare access, and stranded populations.")

    if not cascade_alerts:
        st.success("✅ No critical cascade failures detected in the current scenario parameters.")
    else:
        for idx, alert in enumerate(cascade_alerts):
            st.markdown(f"""
            <div class="cascade-box" style="border-left-color: {alert['severity_color']};">
                <div class="cascade-header" style="color: {alert['severity_color']};">
                    <span>⚠️ CASCADE FAILURE ALERT: {alert['failed_road_name']}</span>
                    <span style="background: {alert['severity_color']}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">
                        {alert['severity']} SEVERITY
                    </span>
                </div>
                <div style="font-size: 0.85rem; color: #475569; margin-bottom: 6px;">
                    <b>Trigger Event:</b> {alert['failed_road_name']} is <b>{alert['road_status']}</b> (Flood Risk: {alert['road_risk']:.0f}/100).
                </div>
                <div class="cascade-chain">
                    <b>Cascade Propagation Chain:</b><br/>
                    {'<br/>&nbsp;&nbsp;↓<br/>'.join(alert['chain_steps'])}
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 0.82rem; margin: 8px 0; background: rgba(255,255,255,0.7); padding: 8px; border-radius: 6px;">
                    <div><b>Dependent Infrastructure:</b> {', '.join([h['name'] for h in alert['dependent_hospitals']] + [s['name'] for s in alert['dependent_shelters']]) or 'Regional corridors'}</div>
                    <div><b>Communities Cut Off:</b> {', '.join(alert['affected_communities']) or 'Coastal settlements'}</div>
                    <div><b>At-Risk Population:</b> <span style="color: #dc2626; font-weight: bold;">{alert['affected_population']:,} residents</span></div>
                </div>
                <div style="font-size: 0.84rem; color: #1e293b; background: #ffffff; border: 1px solid #fbcfe8; border-radius: 6px; padding: 8px 12px; margin-top: 6px;">
                    <b>🚨 Tactical Action Required:</b> {alert['recommended_action']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Interactive action button to jump directly to evacuate affected community
            if alert["affected_communities"]:
                target_comm = alert["affected_communities"][0]
                comm_match = areas_evaluated[areas_evaluated["name"] == target_comm]
                if not comm_match.empty:
                    comm_id = comm_match.iloc[0]["id"]
                    if st.button(f"🧭 Plan Safe Evacuation for {target_comm}", key=f"cascade_btn_{alert['failed_road_id']}_{idx}"):
                        st.session_state.selected_area_id = comm_id
                        recs_c = recommend_shelters_for_area(comm_match.iloc[0], shelters_evaluated, road_dict)
                        if recs_c:
                            st.session_state.active_route = calculate_safe_route(
                                area_id=comm_id,
                                target_shelter_id=recs_c[0]["shelter_id"],
                                areas_df=areas_evaluated,
                                shelters_df=shelters_evaluated,
                                road_dict=road_dict
                            )
                        st.session_state.ai_advisory = None
                        st.toast(f"Focused on {target_comm} with safe route calculated!", icon="🚨")
                        st.rerun()


# ------------------------------------------
# TAB 3: SAFE SHELTER & EVACUATION ROUTING
# ------------------------------------------
with tabs[2]:
    st.markdown("### 🛡️ Safe Shelter Recommendation & Flood-Resilient Routing")
    st.caption("Multi-criteria shelter matching and Dijkstra graph shortest-safest path routing.")

    sel_area = areas_evaluated[areas_evaluated["id"] == st.session_state.selected_area_id].iloc[0]
    shelter_recommendations = recommend_shelters_for_area(sel_area, shelters_evaluated, road_dict)

    top_recommended = shelter_recommendations[0]

    # Two column layout: Shelter ranking + Route Planner
    shelter_col, route_col = st.columns([1, 1])

    with shelter_col:
        st.markdown(f"#### Shelter Suitability for: **{sel_area['name']}**")
        st.markdown(f"""
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 5px solid #16a34a; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #166534; text-transform: uppercase;">Top Recommended Sanctuary</div>
            <div style="font-size: 1.2rem; font-weight: 800; color: #0f172a; margin: 2px 0;">{top_recommended['name']}</div>
            <div style="font-size: 0.85rem; color: #1e293b;">
                Distance: <b>{top_recommended['distance_km']} km</b> • Elevation: <b>{top_recommended['elevation']}m</b> • Capacity: <b>{top_recommended['capacity']:,}</b>
            </div>
            <div style="font-size: 0.78rem; color: #15803d; margin-top: 4px;">
                <b>Rationale:</b> {top_recommended['status_reason']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Allow user to route to an alternative shelter if desired
        shelter_select_map = {f"{s['name']} ({s['status']}) - {s['distance_km']}km": s['shelter_id'] for s in shelter_recommendations}
        chosen_shelter_label = st.selectbox(
            "Select Destination Shelter for Routing:",
            list(shelter_select_map.keys()),
            index=0,
            key="chosen_shelter_select"
        )
        chosen_shelter_id = shelter_select_map[chosen_shelter_label]

        # Other shelters list
        st.markdown("##### All Evaluated Shelters:")
        for s in shelter_recommendations:
            badge_color = s["badge_color"]
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px;">
                <div>
                    <b>{s['name']}</b><br/>
                    <small style="color: #64748b;">Distance: {s['distance_km']} km | Risk: {s['shelter_flood_risk']:.0f}/100 | Elev: {s['elevation']}m</small>
                </div>
                <div style="text-align: right;">
                    <span style="background: {badge_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: bold;">
                        {s['status']}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with route_col:
        # Determine target shelter based on user selection
        target_sid = chosen_shelter_id if 'chosen_shelter_id' in locals() else top_recommended["shelter_id"]
        target_sname = shelters_evaluated.loc[shelters_evaluated["shelter_id"] == target_sid, "name"].values[0]

        st.markdown(f"#### Safe Evacuation Corridor to: **{target_sname}**")

        # Compute safe route if active route is missing or target differs
        if st.session_state.active_route is None or st.session_state.active_route.get("origin_id") != sel_area["id"] or st.session_state.active_route.get("destination_id") != target_sid:
            st.session_state.active_route = calculate_safe_route(
                area_id=sel_area["id"],
                target_shelter_id=target_sid,
                areas_df=areas_evaluated,
                shelters_df=shelters_evaluated,
                road_dict=road_dict
            )

        route_data = st.session_state.active_route

        st.markdown(f"""
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-left: 5px solid #2563eb; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <b style="color: #1e3a8a; font-size: 1rem;">✅ RECOMMENDED SAFE ROUTE</b>
                <span style="font-size: 0.8rem; background: #dbeafe; color: #1e40af; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
                    {route_data['total_distance_km']} km (~{route_data['estimated_travel_time_min']} mins)
                </span>
            </div>
            <div style="margin-top: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #1e293b; line-height: 1.6;">
                {'<br/>&nbsp;&nbsp;↓<br/>'.join(route_data['route_steps'])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if route_data["avoid_roads"]:
            st.markdown("""
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-left: 5px solid #dc2626; border-radius: 8px; padding: 12px;">
                <b style="color: #991b1b; font-size: 0.95rem;">⛔ ROADS TO STRICTLY AVOID:</b>
            """, unsafe_allow_html=True)
            for av in route_data["avoid_roads"]:
                st.markdown(f"""
                <div style="font-size: 0.82rem; color: #7f1d1d; margin-top: 4px;">
                    • <b>{av['name']}</b> — <span style="color: #b91c1c;">{av['hazard_reason']}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------
# TAB 4: GEMINI AI DISASTER COPILOT
# ------------------------------------------
with tabs[3]:
    st.markdown("### 🤖 Gemini AI Grounded Disaster Copilot")
    st.caption("AI advisory layer strictly grounded in calculated risk metrics, population counts, and infrastructure states.")

    sel_area = areas_evaluated[areas_evaluated["id"] == st.session_state.selected_area_id].iloc[0]
    top_shelter = recommend_shelters_for_area(sel_area, shelters_evaluated, road_dict)[0]
    blocked_names = [r["name"] for _, r in roads_evaluated.iterrows() if r["status"] == "BLOCKED"]
    safe_corridor = road_dict.get("R03", {}).get("name", "Waltair Main Road Elevated Corridor (Road C)")

    # Optional dynamic Gemini API key input in UI
    with st.expander("🔑 Optional: Configure Gemini API Key", expanded=False):
        curr_env_key = os.getenv("GEMINI_API_KEY", "")
        ui_key = st.text_input(
            "Gemini API Key",
            value=curr_env_key,
            type="password",
            help="If left blank, the copilot runs smoothly in offline Grounded Demo Mode."
        )
        if ui_key != curr_env_key:
            os.environ["GEMINI_API_KEY"] = ui_key.strip()
            st.session_state.ai_advisory = None
            st.success("API key updated for this session!")

    # Prepare strictly grounded factual JSON payload
    copilot_payload = {
        "area": sel_area["name"],
        "population": int(sel_area["population"]),
        "risk_score": float(sel_area["overall_risk"]),
        "risk_level": sel_area["risk_level"],
        "hospital_access": "COMPROMISED" if blocked_roads_count > 0 else "OPERATIONAL",
        "nearest_safe_shelter": top_shelter["name"],
        "shelter_distance_km": top_shelter["distance_km"],
        "recommended_route": safe_corridor,
        "blocked_roads": blocked_names
    }

    ai_left, ai_right = st.columns([1, 2])

    with ai_left:
        st.markdown("##### Grounded Input Evidence (JSON)")
        st.json(copilot_payload)
        
        gen_advisory_btn = st.button("✨ GENERATE AI ADVISORY", type="primary", use_container_width=True)
        if gen_advisory_btn:
            with st.spinner("Gemini AI synthesizing ground-truth disaster advisory..."):
                st.session_state.ai_advisory = generate_copilot_advisory(copilot_payload)

    with ai_right:
        if st.session_state.ai_advisory is None:
            # Auto generate default for initial view so user doesn't see blank
            st.session_state.ai_advisory = generate_copilot_advisory(copilot_payload)

        adv = st.session_state.ai_advisory

        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 12px;">
                <b style="color: #0f172a; font-size: 1.05rem;">📋 Tactical Disaster Response Briefing</b>
                <span style="font-size: 0.75rem; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                    Source: {adv.get('source', 'Grounded Engine')}
                </span>
            </div>
            
            <div style="margin-bottom: 12px;">
                <b style="color: #1e293b; font-size: 0.85rem; text-transform: uppercase;">1. Situation Assessment:</b>
                <p style="font-size: 0.88rem; color: #334155; margin: 4px 0 0 0; line-height: 1.5;">{adv.get('situation_summary')}</p>
            </div>

            <div style="margin-bottom: 12px;">
                <b style="color: #1e293b; font-size: 0.85rem; text-transform: uppercase;">2. Priority Action Checklist:</b>
                <ul style="font-size: 0.85rem; color: #334155; margin: 4px 0 0 0; padding-left: 20px; line-height: 1.5;">
                    {''.join([f'<li>{act}</li>' for act in adv.get('priority_actions', [])])}
                </ul>
            </div>

            <div style="margin-bottom: 12px;">
                <b style="color: #1e293b; font-size: 0.85rem; text-transform: uppercase;">3. Evacuation Command:</b>
                <p style="font-size: 0.88rem; color: #15803d; font-weight: 600; margin: 4px 0 0 0; line-height: 1.4;">{adv.get('evacuation_recommendation')}</p>
            </div>

            <div style="margin-bottom: 12px;">
                <b style="color: #1e293b; font-size: 0.85rem; text-transform: uppercase;">4. Infrastructure Coordination Directive:</b>
                <p style="font-size: 0.85rem; color: #475569; margin: 4px 0 0 0; line-height: 1.4;">{adv.get('infrastructure_actions')}</p>
            </div>

            <div style="background: #fff1f2; border: 1px solid #fecdd3; border-radius: 6px; padding: 10px; margin-top: 10px;">
                <b style="color: #9f1239; font-size: 0.8rem; text-transform: uppercase;">5. Broadcast-Ready Warning:</b>
                <div style="font-size: 0.86rem; color: #be123c; font-weight: 600; margin-top: 2px;">{adv.get('public_warning')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------
# TAB 5: MULTILINGUAL ALERTS & PHONE SIMULATION
# ------------------------------------------
with tabs[4]:
    st.markdown("### 📱 Multilingual Emergency Alerts & Simulated Phone Broadcast")
    st.caption("Last-mile emergency broadcasting simulation in English and Telugu with Text-to-Speech.")

    sel_area = areas_evaluated[areas_evaluated["id"] == st.session_state.selected_area_id].iloc[0]
    top_shelter = recommend_shelters_for_area(sel_area, shelters_evaluated, road_dict)[0]
    avoid_road_name = [r["name"] for _, r in roads_evaluated.iterrows() if r["status"] == "BLOCKED"]
    avoid_str = avoid_road_name[0] if avoid_road_name else "Beach Road Arterial"
    safe_corridor = road_dict.get("R03", {}).get("name", "Waltair Main Road Elevated Corridor (Road C)")

    # In-tab language selector for instant switching during demonstrations
    st.markdown("##### 🌐 Select Broadcast Language:")
    chosen_lang = st.radio(
        "Broadcast Language",
        list(SUPPORTED_LANGUAGES.keys()),
        index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.selected_language),
        horizontal=True,
        key="tab5_lang_selector"
    )
    st.session_state.selected_language = chosen_lang

    # Build Multilingual Messages
    alert_messages = build_multilingual_messages(
        area_name=sel_area["name"],
        shelter_name=top_shelter["name"],
        safe_route=safe_corridor,
        avoid_road=avoid_str,
        risk_level=sel_area["risk_level"]
    )

    alert_col1, alert_col2 = st.columns([1, 1])

    with alert_col1:
        st.markdown(f"#### 💬 Citizen SMS Alert Preview ({st.session_state.selected_language})")
        
        curr_msg = alert_messages[st.session_state.selected_language]

        # SMS Bubble Mockup
        st.markdown(f"""
        <div class="sms-bubble">
{curr_msg['sms_body']}
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        sms_btn_col1, sms_btn_col2 = st.columns(2)
        with sms_btn_col1:
            if st.button("📢 Dispatch Alert to Broadcast Queue", use_container_width=True):
                st.toast(f"Emergency Alert dispatched to {sel_area['name']} cell broadcast towers!", icon="🚨")
        with sms_btn_col2:
            st.code(curr_msg['sms_body'], language="text")

        st.markdown("---")
        st.markdown("#### 🔊 Audio Voice Alert Synthesizer")
        st.write(f"Language: **{st.session_state.selected_language}**")
        
        lang_code = SUPPORTED_LANGUAGES[st.session_state.selected_language]["code"]

        if st.button("▶ PLAY VOICE ALERT", type="primary", use_container_width=True):
            with st.spinner("Synthesizing voice emergency announcement..."):
                audio_bytes, mime_type = generate_tts_audio(curr_msg["voice_script"], lang_code=lang_code)
                if audio_bytes:
                    st.audio(audio_bytes, format=mime_type, autoplay=True)
                else:
                    st.warning("Voice synthesis offline fallback: " + mime_type)

    with alert_col2:
        st.markdown("#### 📲 Emergency Lock-Screen Simulation")
        curr_msg = alert_messages[st.session_state.selected_language]
        
        # Render Mobile Device Simulation
        phone_html = render_phone_simulation(
            short_msg=curr_msg["short_notification"],
            language_name=st.session_state.selected_language
        )
        st.markdown(phone_html, unsafe_allow_html=True)


# ==========================================
# FOOTER & RESPONSIBLE USE DISCLAIMER
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.76rem; padding: 16px 0; border-top: 1px solid #e2e8f0; margin-top: 20px;">
    <b>CYCLONE-SHIELD AI</b> — Disaster Management Decision-Support Prototype for Visakhapatnam, Andhra Pradesh, India.<br/>
    <i>About / Demo Disclaimer:</i> This is a prototype decision-support system for demonstration purposes. Risk values and recommendations are simulated/model-generated and are not official emergency warnings.
</div>
""", unsafe_allow_html=True)
