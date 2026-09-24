"""
Safe Shelter Recommendation & Evacuation Routing Engine for CYCLONE-SHIELD AI
Evaluates multi-criteria shelter suitability and computes safe, flood-resilient evacuation paths.
"""

from typing import Dict, Any, List, Tuple, Optional
import math
import networkx as nx
import pandas as pd


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def recommend_shelters_for_area(
    area_row: pd.Series,
    shelters_evaluated_df: pd.DataFrame,
    road_dict: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Rank all available cyclone shelters for a specific locality.
    Balances geographic proximity, shelter site safety, and access road viability.
    """
    area_lat = float(area_row["latitude"])
    area_lon = float(area_row["longitude"])
    area_pop = int(area_row["population"])

    shelter_recommendations = []

    for _, s_row in shelters_evaluated_df.iterrows():
        s_lat = float(s_row["latitude"])
        s_lon = float(s_row["longitude"])
        dist_km = haversine_km(area_lat, area_lon, s_lat, s_lon)
        
        s_risk = float(s_row["shelter_flood_risk"])
        s_safety = float(s_row["safety_score"])
        capacity = int(s_row["capacity"])
        base_status = s_row["status"]  # RECOMMENDED, CAUTION, NOT RECOMMENDED

        # Proximity score (0-100): decays with distance beyond immediate neighborhood
        proximity_score = max(5.0, 100.0 - (dist_km * 8.5))

        # Access road check
        road_acc = float(s_row["road_accessibility"])

        # Composite evacuation suitability score (0-100):
        # 40% Site Safety + 35% Proximity + 25% Road Accessibility
        suitability_score = round(s_safety * 0.40 + proximity_score * 0.35 + road_acc * 0.25, 1)

        # Status determination for this specific community
        if base_status == "NOT RECOMMENDED" or s_risk > 60.0 or road_acc < 30.0:
            rec_status = "NOT RECOMMENDED"
            status_reason = f"High shelter site hazard ({s_risk:.0f}/100) or submerged access corridor"
            badge_color = "#dc3545"
        elif suitability_score >= 65.0:
            rec_status = "RECOMMENDED"
            status_reason = f"High ground safety ({s_row['elevation']}m), robust facilities, clear access"
            badge_color = "#28a745"
        else:
            rec_status = "CAUTION"
            status_reason = f"Viable backup sanctuary ({dist_km} km distance)"
            badge_color = "#fd7e14"

        shelter_recommendations.append({
            "shelter_id": s_row["shelter_id"],
            "name": s_row["name"],
            "distance_km": dist_km,
            "elevation": s_row["elevation"],
            "capacity": capacity,
            "shelter_flood_risk": s_risk,
            "safety_score": s_safety,
            "road_accessibility": road_acc,
            "access_road": s_row["access_road"],
            "suitability_score": suitability_score,
            "status": rec_status,
            "status_reason": status_reason,
            "badge_color": badge_color,
            "latitude": s_lat,
            "longitude": s_lon,
            "safety_features": s_row["safety_features"]
        })

    # Sort: RECOMMENDED first, highest suitability, shortest distance
    status_priority = {"RECOMMENDED": 0, "CAUTION": 1, "NOT RECOMMENDED": 2}
    shelter_recommendations.sort(
        key=lambda x: (status_priority.get(x["status"], 3), -x["suitability_score"], x["distance_km"])
    )

    return shelter_recommendations


def build_routing_graph(
    areas_df: pd.DataFrame,
    shelters_df: pd.DataFrame,
    road_dict: Dict[str, Dict[str, Any]]
) -> nx.Graph:
    """
    Construct weighted navigation network.
    Flooded/blocked roads have prohibitive traversal penalty.
    """
    G = nx.Graph()

    # Add Road Segment Nodes
    for road_id, rdata in road_dict.items():
        coords = rdata.get("coordinates", [])
        mid_lat = sum(c[1] for c in coords) / max(1, len(coords)) if coords else 17.72
        mid_lon = sum(c[0] for c in coords) / max(1, len(coords)) if coords else 83.31
        
        G.add_node(
            road_id,
            node_type="road",
            name=rdata["name"],
            lat=mid_lat,
            lon=mid_lon,
            flood_risk=rdata["flood_risk"],
            is_passable=rdata["is_passable"],
            status=rdata["status"]
        )

    # Inter-road junctions based on known geography of Visakhapatnam:
    # R01 (Beach Rd) connects to R02 (Marine Drive) and R03 (Waltair Rd)
    # R03 connects to R04 (Express) and R05 (NH16)
    # R04 connects to R05 (NH16)
    # R05 connects to R06 (Simhachalam)
    inter_road_edges = [
        ("R01", "R02", 3.0),
        ("R01", "R03", 2.2),
        ("R02", "R04", 4.5),
        ("R03", "R04", 3.2),
        ("R03", "R05", 2.8),
        ("R04", "R05", 3.5),
        ("R05", "R06", 4.0),
        ("R04", "R06", 5.0)
    ]

    for u, v, dist in inter_road_edges:
        u_risk = road_dict.get(u, {}).get("flood_risk", 20.0)
        v_risk = road_dict.get(v, {}).get("flood_risk", 20.0)
        u_passable = road_dict.get(u, {}).get("is_passable", True)
        v_passable = road_dict.get(v, {}).get("is_passable", True)

        avg_risk = (u_risk + v_risk) / 2.0
        
        if not u_passable or not v_passable:
            # Prohibitively large weight to avoid flooded routes
            penalty = 10000.0
        else:
            penalty = 1.0 + (avg_risk / 25.0) ** 2.5

        G.add_edge(u, v, weight=dist * penalty, base_dist=dist, road_pair=f"{u}-{v}")

    # Connect Areas to their direct connecting roads
    for _, area in areas_df.iterrows():
        aid = area["id"]
        alat = float(area["latitude"])
        alon = float(area["longitude"])
        G.add_node(aid, node_type="area", name=area["name"], lat=alat, lon=alon)

        # Connect area to matching roads
        for road_id, rdata in road_dict.items():
            if aid in rdata.get("connects", []):
                road_lat = G.nodes[road_id]["lat"]
                road_lon = G.nodes[road_id]["lon"]
                dist = haversine_km(alat, alon, road_lat, road_lon)
                is_p = rdata["is_passable"]
                risk = rdata["flood_risk"]
                weight = dist * (10000.0 if not is_p else (1.0 + (risk / 30.0) ** 2))
                G.add_edge(aid, road_id, weight=weight, base_dist=dist)

    # Connect Shelters to their designated access road
    for _, shelter in shelters_df.iterrows():
        sid = shelter["shelter_id"]
        slat = float(shelter["latitude"])
        slon = float(shelter["longitude"])
        G.add_node(sid, node_type="shelter", name=shelter["name"], lat=slat, lon=slon)
        acc_road = str(shelter.get("access_road_id", ""))

        if acc_road in road_dict:
            road_lat = G.nodes[acc_road]["lat"]
            road_lon = G.nodes[acc_road]["lon"]
            dist = haversine_km(slat, slon, road_lat, road_lon)
            is_p = road_dict[acc_road]["is_passable"]
            risk = road_dict[acc_road]["flood_risk"]
            weight = dist * (10000.0 if not is_p else (1.0 + (risk / 30.0) ** 2))
            G.add_edge(sid, acc_road, weight=weight, base_dist=dist)

    return G


def calculate_safe_route(
    area_id: str,
    target_shelter_id: str,
    areas_df: pd.DataFrame,
    shelters_df: pd.DataFrame,
    road_dict: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute safe evacuation route from selected area to recommended shelter.
    Identifies clear corridors and explicitly pinpoints dangerous roads to avoid.
    """
    G = build_routing_graph(areas_df, shelters_df, road_dict)

    area_name = areas_df.loc[areas_df["id"] == area_id, "name"].values[0] if area_id in areas_df["id"].values else area_id
    shelter_name = shelters_df.loc[shelters_df["shelter_id"] == target_shelter_id, "name"].values[0] if target_shelter_id in shelters_df["shelter_id"].values else target_shelter_id

    # Find shortest path using safest weighted edges
    try:
        path = nx.dijkstra_path(G, source=area_id, target=target_shelter_id, weight="weight")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        # Fallback direct path
        path = [area_id, target_shelter_id]

    # Parse route steps and collect road nodes traversed
    route_steps = []
    roads_traversed = []
    waypoints = []

    for node in path:
        node_info = G.nodes.get(node, {})
        n_type = node_info.get("node_type", "")
        n_name = node_info.get("name", node)
        
        if n_type == "area":
            route_steps.append(f"Origin: {n_name}")
            waypoints.append((node_info["lat"], node_info["lon"]))
        elif n_type == "road":
            road_data = road_dict.get(node, {})
            roads_traversed.append(node)
            status_text = f"(Elevated {road_data.get('elevation_m', 20)}m, Status: {road_data.get('status', 'Passable')})"
            route_steps.append(f"Transit via {n_name} {status_text}")
            # Add road coordinates for mapping
            for coord in road_data.get("coordinates", []):
                waypoints.append((coord[1], coord[0]))
        elif n_type == "shelter":
            route_steps.append(f"Destination Sanctuary: {n_name}")
            waypoints.append((node_info["lat"], node_info["lon"]))

    # Identify roads that should be explicitly AVOIDED
    avoid_list = []
    for r_id, rdata in road_dict.items():
        if not rdata["is_passable"] or rdata["flood_risk"] >= 65.0:
            avoid_list.append({
                "road_id": r_id,
                "name": rdata["name"],
                "flood_risk": rdata["flood_risk"],
                "elevation_m": rdata["elevation_m"],
                "status": rdata["status"],
                "hazard_reason": f"High Flood/Surge Inundation Risk ({rdata['flood_risk']:.0f}/100) - Elevation only {rdata['elevation_m']}m"
            })

    # Total approximate route distance
    total_km = 0.0
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i + 1])
        if edge_data and "base_dist" in edge_data:
            total_km += edge_data["base_dist"]
        else:
            total_km += 1.5

    return {
        "origin_id": area_id,
        "origin_name": area_name,
        "destination_id": target_shelter_id,
        "destination_name": shelter_name,
        "path_nodes": path,
        "route_steps": route_steps,
        "roads_traversed": roads_traversed,
        "avoid_roads": avoid_list,
        "total_distance_km": round(max(1.2, total_km), 1),
        "estimated_travel_time_min": round(max(8, total_km * 3.5)),
        "waypoints": waypoints
    }
