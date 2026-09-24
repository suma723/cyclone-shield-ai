import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.data_loader import load_areas, load_hospitals, load_shelters, load_roads
from src.risk_engine import evaluate_all_areas
from src.infrastructure import evaluate_roads, evaluate_hospitals, evaluate_shelters
from src.cascade import analyze_cascade_impacts
from src.evacuation import recommend_shelters_for_area, calculate_safe_route
from src.gemini_advisor import generate_copilot_advisory
from src.alerts import build_multilingual_messages, generate_tts_audio

areas = load_areas()
roads_json = load_roads()
hospitals = load_hospitals()
shelters = load_shelters()

areas_eval = evaluate_all_areas(areas, 3.2, 280.0, 145)
roads_eval, r_dict = evaluate_roads(roads_json, 3.2, 280.0, 145)
hosps_eval = evaluate_hospitals(hospitals, r_dict, 3.2, 280.0, 145)
shelters_eval = evaluate_shelters(shelters, r_dict, 3.2, 280.0, 145)

cascades = analyze_cascade_impacts(areas_eval, hosps_eval, shelters_eval, r_dict)
print(f"Cascade alerts count: {len(cascades)}")
if cascades:
    print(f"First cascade alert: {cascades[0]['failed_road_name']}")
    for step in cascades[0]['chain_steps']:
        print(f"  - {step}")

shelter_recs = recommend_shelters_for_area(areas_eval.iloc[0], shelters_eval, r_dict)
print(f"Top shelter: {shelter_recs[0]['name']} ({shelter_recs[0]['status']})")

route = calculate_safe_route('A01', shelter_recs[0]['shelter_id'], areas_eval, shelters_eval, r_dict)
print("Route steps:")
for step in route['route_steps']:
    print(f"  - {step}")
print("Avoid roads:", [r['name'] for r in route['avoid_roads']])

payload = {
    'area': 'RK Beach Coastal Sector',
    'population': 18500,
    'risk_score': 88,
    'risk_level': 'CRITICAL',
    'hospital_access': 'POOR',
    'nearest_safe_shelter': 'MVP AU Campus Cyclone Shelter',
    'shelter_distance_km': 3.2,
    'recommended_route': 'Waltair Main Road (Road C)',
    'blocked_roads': ['Beach Road Coastal Arterial (Road A)']
}
adv = generate_copilot_advisory(payload)
print(f"Advisory Source: {adv['source']}")
print(f"Situation Summary: {adv['situation_summary']}")

msgs = build_multilingual_messages('RK Beach Coastal Sector', 'MVP AU Shelter', 'Waltair Road C', 'Beach Road A', 'CRITICAL')
print(f"Telugu Notification: {msgs['Telugu (తెలుగు)']['short_notification']}")

audio_bytes, mime = generate_tts_audio(msgs['English']['voice_script'], 'en')
print(f"TTS Audio generated: {len(audio_bytes)} bytes, format: {mime}")
print("PIPELINE TEST PASSED SUCCESSFULLY!")
