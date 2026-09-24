"""
Gemini AI Disaster Copilot for CYCLONE-SHIELD AI
Provides evidence-grounded tactical disaster advisories.
Strictly grounds all reasoning in calculated risk metrics without hallucinating numbers.
Includes resilient fallback demo advisor for 100% offline hackathon execution.
"""

import os
import json
from typing import Dict, Any, List


def generate_fallback_advisory(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic, highly structured disaster advisory grounded purely on calculated inputs.
    Used when Gemini API key is not configured or network is offline.
    """
    area = data.get("area", "Coastal Visakhapatnam")
    pop = data.get("population", 18500)
    risk_score = data.get("risk_score", 85)
    risk_level = data.get("risk_level", "CRITICAL")
    hosp_access = data.get("hospital_access", "COMPROMISED")
    shelter = data.get("nearest_safe_shelter", "MVP AU Campus Cyclone Shelter")
    shelter_dist = data.get("shelter_distance_km", 3.2)
    rec_route = data.get("recommended_route", "Waltair Main Road Elevated Corridor (Road C)")
    blocked_roads = data.get("blocked_roads", ["Beach Road Coastal Arterial (Road A)"])
    blocked_str = ", ".join(blocked_roads) if blocked_roads else "None reported"

    return {
        "status": "success",
        "source": "Cyclone-Shield Grounded Advisory Engine (Deterministic Local Mode)",
        "grounded_input": data,
        "situation_summary": (
            f"Urgent Cyclone Vulnerability Warning for {area}: Current modeled hazard index is {risk_score}/100 "
            f"({risk_level}). Approximately {pop:,} residents face acute tidal surge exposure. "
            f"Primary arterial corridor [{blocked_str}] is impassable due to storm surge inundation, "
            f"leaving emergency medical accessibility rated as {hosp_access}."
        ),
        "priority_actions": [
            f"[T-0 to T-2h] Evacuate {area} residents from low-lying shorelines to {shelter}.",
            f"[T-0 to T-3h] Enforce physical barricades on {blocked_str} to prevent vehicular entrapment.",
            f"[T-2 to T-6h] Stage NDRF flood rescue teams along {rec_route} to maintain emergency transit.",
            f"[T-4 to T-12h] Pre-position emergency generators, clean water, and surgical supplies at {shelter}."
        ],
        "evacuation_recommendation": (
            f"Immediate evacuation advised for {pop:,} vulnerable citizens in {area}. "
            f"Transit immediately towards {shelter} ({shelter_dist} km away). "
            f"Navigate exclusively via {rec_route}. STRICTLY AVOID {blocked_str}."
        ),
        "infrastructure_actions": (
            f"Regional trauma coordination: Since {blocked_str} is flooded, direct all critical trauma "
            f"ambulances inland via {rec_route}. Activate emergency backup generators and fuel reserves "
            f"at tertiary hospitals and designated relief hubs."
        ),
        "public_warning": (
            f"🚨 EMERGENCY WARNING: Severe storm surge hazard in {area}. Evacuate immediately to {shelter} "
            f"via {rec_route}. Do NOT take {blocked_str}. Dial 1070 for State Disaster Helpline."
        )
    }


def get_gemini_api_key() -> str:
    """
    Retrieve Gemini API key from environment variable or Streamlit secrets safely.
    Supports st.secrets["GEMINI_API_KEY"] on Streamlit Community Cloud.
    """
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key

    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            secret_val = st.secrets["GEMINI_API_KEY"]
            if secret_val and str(secret_val).strip():
                return str(secret_val).strip()
    except Exception:
        pass

    return ""


def generate_copilot_advisory(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate disaster response advisory using Google Gemini API if available,
    or smoothly fallback to local grounded advisory engine.
    """
    api_key = get_gemini_api_key()

    if not api_key:
        return generate_fallback_advisory(data)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Use standard modern flash model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

        prompt = f"""
You are the Lead Disaster Response Operations Director for CYCLONE-SHIELD AI in Visakhapatnam, Andhra Pradesh, India.
You must generate an evidence-grounded tactical disaster advisory.

CRITICAL RULES:
1. Ground your analysis strictly and ONLY on the calculated facts provided below.
2. DO NOT invent, hallucinate, or alter any numbers, road names, shelter names, or population counts.
3. Output MUST be valid JSON conforming to the requested schema.

CALCULATED EVIDENCE:
{json.dumps(data, indent=2)}

OUTPUT SCHEMA:
{{
  "situation_summary": "Concise 2-3 sentence situation assessment with exact numbers",
  "priority_actions": ["Array of 4 time-stamped tactical actions"],
  "evacuation_recommendation": "Direct evacuation command naming safe shelter and route",
  "infrastructure_actions": "Clear guidance for transport police, NDRF, and hospital coordination",
  "public_warning": "Urgent SMS-length warning message for citizens"
}}
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        parsed = json.loads(text)
        parsed["status"] = "success"
        parsed["source"] = "Google Gemini 1.5 Flash (Live Grounded Reasoning)"
        parsed["grounded_input"] = data
        return parsed

    except Exception as e:
        # Fallback gracefully with error annotation
        fallback = generate_fallback_advisory(data)
        fallback["source"] = f"Cyclone-Shield Grounded Advisory Engine (API Fallback: {type(e).__name__})"
        return fallback
