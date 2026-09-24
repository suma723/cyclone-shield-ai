"""
UI Helpers, Custom CSS and Visualization Components for CYCLONE-SHIELD AI
Provides a clean, government-grade disaster dashboard aesthetic and phone simulation widgets.
"""

import base64
from typing import Dict, Any


def get_custom_css() -> str:
    """Return polished custom CSS styling for government/disaster-management UI."""
    return """
    <style>
        /* Import clean corporate font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        /* Top Header Banner */
        .disaster-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border-left: 6px solid #ef4444;
            padding: 1.2rem 1.8rem;
            border-radius: 8px;
            color: #f8fafc;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .disaster-header h1 {
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin: 0;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .disaster-header p {
            font-size: 0.95rem;
            color: #94a3b8;
            margin: 6px 0 0 0;
        }

        .badge-live-gov {
            background-color: #ef4444;
            color: white;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        /* KPI Cards Container */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 12px;
            margin-bottom: 1.5rem;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            border-top: 4px solid #3b82f6;
            transition: transform 0.15s ease;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }

        .kpi-title {
            font-size: 0.75rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .kpi-value {
            font-size: 1.6rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.2;
        }

        .kpi-sub {
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 4px;
        }

        /* Cascade Alert Box */
        .cascade-box {
            background: #fff1f2;
            border: 1px solid #fecdd3;
            border-left: 5px solid #e11d48;
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1.2rem;
        }

        .cascade-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 800;
            color: #9f1239;
            font-size: 1rem;
            margin-bottom: 8px;
        }

        .cascade-chain {
            background: #ffffff;
            border: 1px dashed #fda4af;
            border-radius: 6px;
            padding: 10px 14px;
            margin: 8px 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: #881337;
            line-height: 1.6;
        }

        /* Mobile Simulation Mockup */
        .phone-mockup {
            width: 320px;
            margin: 0 auto;
            background: #0f172a;
            border: 10px solid #1e293b;
            border-radius: 36px;
            padding: 16px 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
            color: #f8fafc;
            position: relative;
        }

        .phone-notch {
            width: 110px;
            height: 18px;
            background: #1e293b;
            border-radius: 0 0 10px 10px;
            margin: -16px auto 14px auto;
        }

        .phone-clock {
            text-align: center;
            font-size: 2.2rem;
            font-weight: 300;
            color: #f1f5f9;
            margin-bottom: 4px;
        }

        .phone-date {
            text-align: center;
            font-size: 0.8rem;
            color: #94a3b8;
            margin-bottom: 16px;
        }

        .phone-alert-card {
            background: rgba(225, 29, 72, 0.92);
            backdrop-filter: blur(8px);
            border-radius: 14px;
            padding: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            animation: pulse-border 2s infinite;
        }

        @keyframes pulse-border {
            0% { box-shadow: 0 0 0 0 rgba(225, 29, 72, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(225, 29, 72, 0); }
            100% { box-shadow: 0 0 0 0 rgba(225, 29, 72, 0); }
        }

        .phone-alert-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
            color: #fecdd3;
        }

        .phone-alert-msg {
            font-size: 0.84rem;
            font-weight: 600;
            line-height: 1.35;
            color: #ffffff;
            margin-bottom: 8px;
        }

        /* SMS Terminal Preview */
        .sms-bubble {
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 14px 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.86rem;
            color: #0f172a;
            white-space: pre-wrap;
            line-height: 1.5;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
        }
    </style>
    """


def render_kpi(title: str, value: str, sub: str = "", border_color: str = "#3b82f6") -> str:
    """Generate HTML string for a clean KPI metric card."""
    return f"""
    <div class="kpi-card" style="border-top-color: {border_color};">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value" style="color: {border_color if border_color in ['#dc3545', '#e11d48'] else '#0f172a'};">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """


def render_phone_simulation(
    short_msg: str,
    language_name: str,
    time_str: str = "09:42",
    date_str: str = "Thursday, Cyclone Alert Active"
) -> str:
    """Generate styled smartphone lock-screen emergency alert mockup."""
    return f"""
    <div class="phone-mockup">
        <div class="phone-notch"></div>
        <div class="phone-clock">{time_str}</div>
        <div class="phone-date">{date_str}</div>
        
        <div class="phone-alert-card">
            <div class="phone-alert-header">
                <span>🚨 EMERGENCY CYCLONE ALERT</span>
                <span>CRITICAL</span>
            </div>
            <div class="phone-alert-msg">
                "{short_msg}"
            </div>
            <div style="font-size: 0.72rem; color: #ffe4e6; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.25); padding-top: 6px;">
                <span>Language: <b>{language_name}</b></span>
                <span style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">Cell Broadcast Channel 4370</span>
            </div>
        </div>
        <div style="text-align: center; margin-top: 16px; font-size: 0.7rem; color: #64748b;">
            <b>Prototype Emergency Alert Simulation</b><br/>
            (Simulated Last-Mile Broadcast)
        </div>
    </div>
    """
