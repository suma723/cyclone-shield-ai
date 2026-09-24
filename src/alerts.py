"""
Multilingual Alerts, Voice Synthesizer & Lock-Screen Simulation for CYCLONE-SHIELD AI
Generates action-oriented emergency SMS, voice audio, and interactive lockscreen previews
in English and Telugu (with Hindi & Tamil readiness).
"""

import os
import io
from typing import Dict, Any, Tuple


# Language configurations
SUPPORTED_LANGUAGES = {
    "English": {"code": "en", "native_name": "English"},
    "Telugu (తెలుగు)": {"code": "te", "native_name": "తెలుగు"},
    "Hindi (हिन्दी)": {"code": "hi", "native_name": "हिन्दी"},
    "Tamil (தமிழ்)": {"code": "ta", "native_name": "தமிழ்"}
}


def build_multilingual_messages(
    area_name: str,
    shelter_name: str,
    safe_route: str,
    avoid_road: str,
    risk_level: str
) -> Dict[str, Dict[str, str]]:
    """
    Format authoritative, clear, action-oriented cyclone alerts across languages.
    """
    messages = {}

    # 1. English
    messages["English"] = {
        "title": "🚨 CYCLONE EMERGENCY ALERT - APSDMA / VISAKHAPATNAM",
        "risk_badge": f"RISK LEVEL: {risk_level}",
        "sms_body": (
            f"🚨 CYCLONE ALERT: Severe flooding risk detected in {area_name}.\n"
            f"Immediate evacuation recommended.\n\n"
            f"📍 MOVE TO: {shelter_name}\n"
            f"🛣️ RECOMMENDED ROUTE: {safe_route}\n"
            f"⛔ STRICTLY AVOID: {avoid_road}\n\n"
            f"Emergency Helpline: Dial 1070 / 112. Stay indoors once sheltered."
        ),
        "voice_script": (
            f"Cyclone emergency warning for {area_name}. Severe storm surge hazard detected. "
            f"Evacuate immediately to {shelter_name} using {safe_route}. "
            f"Do not use {avoid_road}. For immediate rescue assistance, dial 1070."
        ),
        "short_notification": f"Evacuate {area_name} now to {shelter_name} via {safe_route}. Avoid {avoid_road}."
    }

    # 2. Telugu
    messages["Telugu (తెలుగు)"] = {
        "title": "🚨 తుఫాను అత్యవసర హెచ్చరిక - విశాఖపట్నం",
        "risk_badge": f"ప్రమాద తీవ్రత: {risk_level}",
        "sms_body": (
            f"🚨 తుఫాను హెచ్చరిక: {area_name} పరిధిలో తీవ్రమైన వరద ప్రమాదం గుర్తించబడింది.\n"
            f"తక్షణమే సురక్షిత ప్రాంతాలకు తరలివెళ్లండి.\n\n"
            f"📍 సురక్షిత ఆశ్రయం: {shelter_name}\n"
            f"🛣️ సిఫార్సు చేసిన మార్గం: {safe_route}\n"
            f"⛔ నివారించవలసిన రోడ్డు: {avoid_road}\n\n"
            f"విపత్తు సహాయ వాణి: 1070 లేదా 112 కు కాల్ చేయండి."
        ),
        "voice_script": (
            f"తుఫాను అత్యవసర హెచ్చరిక! {area_name} పరిధిలో తీవ్ర వరద ముప్పు పొంచి ఉంది. "
            f"వెంటనే {safe_route} ద్వారా {shelter_name} కి వెళ్ళండి. "
            f"{avoid_road} ను ఎట్టి పరిస్థితుల్లో ఉపయోగించకండి. అత్యవసర సహాయం కొరకు 1070 కు కాల్ చేయండి."
        ),
        "short_notification": f"{area_name} లో తక్షణ తరలింపు: {safe_route} ద్వారా {shelter_name} కి వెళ్లండి. {avoid_road} ను నివారించండి."
    }

    # 3. Hindi
    messages["Hindi (हिन्दी)"] = {
        "title": "🚨 चक्रवात आपातकालीन चेतावनी - विशाखापट्टनम",
        "risk_badge": f"जोखिम स्तर: {risk_level}",
        "sms_body": (
            f"🚨 चक्रवात चेतावनी: {area_name} में गंभीर बाढ़ का खतरा दर्ज किया गया है।\n"
            f"तत्काल सुरक्षित स्थान पर जाएं।\n\n"
            f"📍 सुरक्षित आश्रय: {shelter_name}\n"
            f"🛣️ सुरक्षित मार्ग: {safe_route}\n"
            f"⛔ न जाएं: {avoid_road}\n\n"
            f"आपदा हेल्पलाइन: 1070 या 112 डायल करें।"
        ),
        "voice_script": (
            f"चक्रवात आपातकालीन चेतावनी! {area_name} में भारी जलभराव का खतरा है। "
            f"कृपया तुरंत {safe_route} से होते हुए {shelter_name} पहुंचे। "
            f"{avoid_road} पर बिल्कुल न जाएं।"
        ),
        "short_notification": f"{area_name} से तत्काल सुरक्षित आश्रय {shelter_name} की ओर {safe_route} से जाएं।"
    }

    # 4. Tamil
    messages["Tamil (தமிழ்)"] = {
        "title": "🚨 புயல் அவசர எச்சரிக்கை - விசாகப்பட்டினம்",
        "risk_badge": f"ஆபத்து நிலை: {risk_level}",
        "sms_body": (
            f"🚨 புயல் எச்சரிக்கை: {area_name} பகுதியில் கடுமையான வெள்ள அபாயம் கண்டறியப்பட்டுள்ளது.\n"
            f"உடனடியாக பாதுகாப்பான இடத்திற்கு செல்லவும்.\n\n"
            f"📍 பாதுகாப்பான தங்குமிடம்: {shelter_name}\n"
            f"🛣️ பாதுகாப்பான பாதை: {safe_route}\n"
            f"⛔ தவிர்க்க வேண்டிய சாலை: {avoid_road}\n\n"
            f"பேரிடர் உதவி எண்: 1070 / 112."
        ),
        "voice_script": (
            f"புயல் அவசர எச்சரிக்கை! {area_name} பகுதியில் உடனடியாக வெளியேறி {safe_route} வழியாக {shelter_name} தங்குமிடத்திற்கு செல்லவும்."
        ),
        "short_notification": f"{area_name} இலிருந்து {safe_route} வழியாக {shelter_name} தங்குமிடம் செல்லவும்."
    }

    return messages


def generate_tts_audio(text: str, lang_code: str = "en") -> Tuple[bytes, str]:
    """
    Generate Text-to-Speech audio bytes using gTTS.
    Returns (audio_bytes, mime_type).
    Falls back gracefully if network is unavailable.
    """
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read(), "audio/mp3"
    except Exception as e:
        # Fallback silent/header minimal mp3 or error notice
        return b"", f"TTS Unavailable: {type(e).__name__}"
