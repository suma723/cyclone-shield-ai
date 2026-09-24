"""
Cascade Dependency & Network Impact Engine for CYCLONE-SHIELD AI
Analyzes chain-reaction failures across Roads, Critical Healthcare, and Communities:
Road Failure -> Infrastructure Isolation -> Community Access Cutoff -> Escalated Emergency Risk
"""

from typing import Dict, Any, List
import networkx as nx
import pandas as pd


def build_dependency_graph(
    areas_df: pd.DataFrame,
    hospitals_df: pd.DataFrame,
    shelters_df: pd.DataFrame,
    road_dict: Dict[str, Dict[str, Any]]
) -> nx.DiGraph:
    """
    Construct a directed dependency graph:
    Communities (Areas) depend on Roads.
    Roads provide access to Hospitals and Shelters.
    """
    G = nx.DiGraph()

    # Add Road nodes
    for road_id, rdata in road_dict.items():
        G.add_node(road_id, type="road", name=rdata["name"], is_passable=rdata["is_passable"], risk=rdata["flood_risk"])

    # Add Community Area nodes
    for _, area in areas_df.iterrows():
        a_id = area["id"]
        G.add_node(a_id, type="community", name=area["name"], population=int(area["population"]))

    # Add Hospital nodes
    for _, hosp in hospitals_df.iterrows():
        h_id = hosp["hospital_id"]
        G.add_node(h_id, type="hospital", name=hosp["name"], capacity=int(hosp["capacity"]), importance=hosp["importance"])
        # Edge from road to hospital
        r1 = str(hosp.get("primary_access_road", ""))
        r2 = str(hosp.get("secondary_access_road", ""))
        if r1 in road_dict:
            G.add_edge(r1, h_id, role="primary")
        if r2 in road_dict:
            G.add_edge(r2, h_id, role="secondary")

    # Add Shelter nodes
    for _, shelter in shelters_df.iterrows():
        s_id = shelter["shelter_id"]
        G.add_node(s_id, type="shelter", name=shelter["name"], capacity=int(shelter["capacity"]))
        r_acc = str(shelter.get("access_road_id", ""))
        if r_acc in road_dict:
            G.add_edge(r_acc, s_id, role="access")

    # Connect Communities to Roads based on connectivity
    for road_id, rdata in road_dict.items():
        for conn_id in rdata.get("connects", []):
            if conn_id.startswith("A") and conn_id in G:
                # Community connects to road
                G.add_edge(conn_id, road_id)
                G.add_edge(road_id, conn_id)

    return G


def analyze_cascade_impacts(
    areas_df: pd.DataFrame,
    hospitals_df: pd.DataFrame,
    shelters_df: pd.DataFrame,
    road_dict: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Evaluate cascade impacts when roads become impassable or severely waterlogged.
    Identifies dependent hospitals, stranded shelters, and affected populations.
    """
    G = build_dependency_graph(areas_df, hospitals_df, shelters_df, road_dict)
    cascade_alerts = []

    # Map area IDs to names and population for fast lookup
    area_lookup = {row["id"]: {"name": row["name"], "pop": int(row["population"])} for _, row in areas_df.iterrows()}
    hospital_lookup = {row["hospital_id"]: row.to_dict() for _, row in hospitals_df.iterrows()}
    shelter_lookup = {row["shelter_id"]: row.to_dict() for _, row in shelters_df.iterrows()}

    for road_id, rdata in road_dict.items():
        # Check if road is compromised
        if not rdata["is_passable"] or rdata["flood_risk"] >= 60.0:
            failed_road_name = rdata["name"]
            road_status = rdata["status"]

            # 1. Dependent Hospitals
            dependent_hospitals = []
            for h_id, hdata in hospital_lookup.items():
                p_road = str(hdata.get("primary_access_road", ""))
                s_road = str(hdata.get("secondary_access_road", ""))
                if p_road == road_id:
                    s_road_passable = road_dict.get(s_road, {}).get("is_passable", True)
                    dependent_hospitals.append({
                        "id": h_id,
                        "name": hdata["name"],
                        "importance": hdata["importance"],
                        "has_backup_route": s_road_passable,
                        "backup_road_name": road_dict.get(s_road, {}).get("name", "None")
                    })

            # 2. Dependent Shelters
            dependent_shelters = []
            for s_id, sdata in shelter_lookup.items():
                acc_road = str(sdata.get("access_road_id", ""))
                if acc_road == road_id:
                    dependent_shelters.append({
                        "id": s_id,
                        "name": sdata["name"],
                        "capacity": sdata["capacity"]
                    })

            # 3. Affected Communities (Localities that rely on this road)
            connected_areas = [conn for conn in rdata.get("connects", []) if conn.startswith("A")]
            total_affected_pop = sum(area_lookup[aid]["pop"] for aid in connected_areas if aid in area_lookup)
            affected_community_names = [area_lookup[aid]["name"] for aid in connected_areas if aid in area_lookup]

            if dependent_hospitals or dependent_shelters or total_affected_pop > 0:
                # Determine Severity
                if rdata["flood_risk"] >= 75 and any(h["has_backup_route"] is False for h in dependent_hospitals):
                    severity = "CRITICAL"
                    sev_color = "#dc3545"
                elif rdata["flood_risk"] >= 70 or total_affected_pop > 25000:
                    severity = "HIGH"
                    sev_color = "#fd7e14"
                else:
                    severity = "MEDIUM"
                    sev_color = "#ffc107"

                # Construct chain of impact description
                hosp_names = ", ".join([h["name"] for h in dependent_hospitals]) if dependent_hospitals else "Secondary Clinics"
                comm_names = ", ".join(affected_community_names[:3]) if affected_community_names else "Adjacent Sectors"
                
                chain_steps = [
                    f"{failed_road_name} ({road_status}, Risk: {rdata['flood_risk']:.0f}/100)",
                    f"Access to {hosp_names} compromised",
                    f"{comm_names} ({total_affected_pop:,} residents) lose direct emergency corridor",
                    f"Critical ambulance response delayed by 25-45 minutes"
                ]

                # Recommended actionable response
                backup_routes = [h["backup_road_name"] for h in dependent_hospitals if h["has_backup_route"]]
                if backup_routes:
                    action = (
                        f"Deploy NDRF/SDRF traffic control. Divert urgent trauma cases via "
                        f"{backup_routes[0]}. Issue immediate cell-broadcast alert instructing "
                        f"citizens in {comm_names} to avoid {failed_road_name}."
                    )
                else:
                    action = (
                        f"Emergency corridor severed! Deploy water rescue boats and aerial airlift "
                        f"contingency. Direct all local casualties to regional backup medical stations."
                    )

                cascade_alerts.append({
                    "failed_road_id": road_id,
                    "failed_road_name": failed_road_name,
                    "road_risk": rdata["flood_risk"],
                    "road_status": road_status,
                    "severity": severity,
                    "severity_color": sev_color,
                    "dependent_hospitals": dependent_hospitals,
                    "dependent_shelters": dependent_shelters,
                    "affected_communities": affected_community_names,
                    "affected_population": total_affected_pop,
                    "chain_steps": chain_steps,
                    "recommended_action": action
                })

    # Sort alerts by severity (CRITICAL first, then HIGH, then MEDIUM)
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    cascade_alerts.sort(key=lambda x: severity_order.get(x["severity"], 4))

    return cascade_alerts
