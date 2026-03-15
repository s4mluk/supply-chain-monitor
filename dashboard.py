import streamlit as st
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

st.set_page_config(
    page_title="Supply Chain Risk Monitor",
    page_icon="•",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== Custom CSS — ammattimainen ulkoasu ==========
st.markdown("""
<style>
    /* Typografia ja tilat */
    .stApp { max-width: 1400px; margin: 0 auto; }
    h1, h2, h3 { font-family: 'Segoe UI', system-ui, sans-serif; letter-spacing: -0.02em; }
    
    /* Header-banner */
    .dashboard-header {
        background: linear-gradient(135deg, #0d7377 0%, #14a3a8 100%);
        color: white;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(13, 115, 119, 0.2);
    }
    .dashboard-header h1 { color: white; margin: 0; font-size: 1.6rem; font-weight: 600; }
    .dashboard-header .subtitle { color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-top: 0.25rem; }
    
    /* Status-pilli (reaaliaika / historiallinen) */
    .status-pill {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .status-pill.live { background: #d4edda; color: #155724; }
    .status-pill.historical { background: #cce5ff; color: #004085; }
    
    /* Risk-badge (iso, värikoodattu) */
    .risk-badge {
        display: inline-block;
        padding: 0.5rem 1.25rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-bottom: 1rem;
    }
    .risk-badge.LOW { background: #d4edda; color: #155724; }
    .risk-badge.MEDIUM { background: #fff3cd; color: #856404; }
    .risk-badge.HIGH { background: #f8d7da; color: #721c24; }
    .risk-badge.CRITICAL { background: #721c24; color: #fff; }
    
    /* Metric-kortit — kevyt reunus ja tasainen ulkoasu */
    [data-testid="stMetric"] {
        background: #fff;
        padding: 1rem 1.25rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    [data-testid="stMetric"] label { font-size: 0.8rem; font-weight: 500; color: #6c757d; text-transform: uppercase; letter-spacing: 0.03em; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 700; color: #212529; }
    
    /* Formula-caption */
    .formula-bar {
        font-size: 0.8rem;
        color: #6c757d;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    
    /* Section-otsikot */
    .section-title { font-size: 1rem; font-weight: 600; color: #0d7377; margin-bottom: 0.75rem; }
    
    /* Executive summary — card-tyyli */
    .exec-summary {
        background: linear-gradient(to right, #f0f9f9 0%, #fff 100%);
        border-left: 4px solid #0d7377;
        padding: 1rem 1.25rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        font-size: 0.95rem;
        line-height: 1.55;
    }
    
    /* Risk driver -rivit */
    .risk-driver { padding: 0.6rem 0; border-bottom: 1px solid #f1f3f5; }
    .risk-driver:last-child { border-bottom: none; }
    .risk-driver .severity-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 0.5rem; }
    .risk-driver .severity-dot.LOW { background: #ffc107; }
    .risk-driver .severity-dot.MEDIUM { background: #fd7e14; }
    .risk-driver .severity-dot.HIGH { background: #dc3545; }
    
    /* Toimenpidesarake */
    .action-item { padding: 0.5rem 0; padding-left: 1rem; border-left: 3px solid #0d7377; margin-bottom: 0.5rem; background: #f8f9fa; border-radius: 0 6px 6px 0; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background: #f1f3f5; }
    [data-testid="stSidebar"] .stMarkdown { font-weight: 500; }
    
    /* Footer */
    .dashboard-footer { font-size: 0.75rem; color: #adb5bd; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent
MAIN_FILE = BASE_DIR / "main.py"
ANALYSIS_FILE = BASE_DIR / "latest_analysis.json"

# ========== Sidebar ==========
with st.sidebar:
    st.markdown("### Controls")
    mode = st.radio("Mode", ["Reaaliaikainen", "Historiallinen"], index=0, label_visibility="collapsed")
    target_date = None
    if mode == "Historiallinen":
        target_date = st.date_input(
            "Päivämäärä",
            value=date(2024, 6, 15),
            min_value=date(2020, 1, 1),
            max_value=date.today(),
        )
        st.caption("Uutiset, hinnat ja sää valitulta päivältä")
    if st.button("Suorita analyysi", type="primary", use_container_width=True):
        with st.spinner("Ajetaan analyysi..."):
            cmd = [sys.executable, str(MAIN_FILE)]
            if target_date:
                cmd.append(str(target_date))
            r = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
            if r.stdout:
                st.text(r.stdout)
            if r.stderr:
                st.error(r.stderr)
            if r.returncode == 0:
                st.rerun()
            else:
                st.error("Analyysin suoritus epäonnistui.")

# ========== Data ==========
if not ANALYSIS_FILE.exists():
    st.info("Suorita analyysi sivupalkista ladataksesi data.")
    st.stop()

with ANALYSIS_FILE.open(encoding="utf-8") as f:
    data = json.load(f)

query_date = data.get("query_date", "realtime")
risk_level = data.get("risk_level", "MEDIUM")
ts = data.get("timestamp", "")[:19].replace("T", " ")

# ========== Header ==========
st.markdown("""
<div class="dashboard-header">
    <h1>Supply Chain Risk Monitor</h1>
    <div class="subtitle">Consumer Goods · Asia Sourcing Exposure</div>
</div>
""", unsafe_allow_html=True)

# Status pill
pill_class = "live" if query_date == "realtime" else "historical"
pill_text = "Reaaliaikainen" if query_date == "realtime" else f"Historiallinen — {query_date}"
st.markdown(f'<span class="status-pill {pill_class}">{pill_text}</span>', unsafe_allow_html=True)

# Risk badge
st.markdown(f'<span class="risk-badge {risk_level}">{risk_level} · {data.get("overall_risk_score", 0)}/10</span>', unsafe_allow_html=True)

# Formula
formula = data.get("scoring_formula") or "0.40×News + 0.30×Logistics + 0.20×Commodity + 0.10×Weather"
st.markdown(f'<div class="formula-bar"><strong>Risk scoring:</strong> Overall = {formula} (scores 1–10)</div>', unsafe_allow_html=True)

# ========== Metrics ==========
sb = data.get("signal_breakdown", {})
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Overall Risk", f"{data.get('overall_risk_score', '–')}/10", risk_level)
c2.metric("News", f"{sb.get('news_risk', '–')}/10", None)
c3.metric("Logistics", f"{sb.get('logistics_risk', '–')}/10", None)
c4.metric("Commodity", f"{sb.get('commodity_risk', '–')}/10", None)
c5.metric("Weather", f"{sb.get('weather_risk', '–')}/10", None)

# Port weather risk
port_risk = data.get("port_weather_risk")
if port_risk and isinstance(port_risk, dict):
    with st.expander("Port weather risk"):
        for port, level in port_risk.items():
            st.markdown(f"**{port}:** {level}")

st.divider()

# ========== Executive Summary ==========
st.markdown('<p class="section-title">Executive Summary</p>', unsafe_allow_html=True)
st.markdown(f'<div class="exec-summary">{data.get("executive_summary", "")}</div>', unsafe_allow_html=True)

st.divider()

# ========== Risk Drivers & Actions ==========
col_left, col_right = st.columns(2)
with col_left:
    st.markdown('<p class="section-title">Top Risk Drivers</p>', unsafe_allow_html=True)
    for d in data.get("top_risk_drivers", []):
        sev = d.get("severity", "")
        dot_class = sev if sev in ("LOW", "MEDIUM", "HIGH") else "LOW"
        st.markdown(f"""
        <div class="risk-driver">
            <span class="severity-dot {dot_class}"></span><strong>{d.get("driver", "")}</strong><br>
            <span style="font-size:0.85rem;color:#6c757d;">{d.get("explanation", "")}</span>
        </div>
        """, unsafe_allow_html=True)

with col_right:
    st.markdown('<p class="section-title">Recommended Actions</p>', unsafe_allow_html=True)
    for action in data.get("recommended_actions", []):
        st.markdown(f'<div class="action-item">{action}</div>', unsafe_allow_html=True)

# Expanders
if data.get("key_assumptions"):
    with st.expander("Key assumptions"):
        for a in data["key_assumptions"]:
            st.markdown(f"- {a}")
if data.get("data_limitations"):
    with st.expander("Data limitations"):
        st.caption(data["data_limitations"])
with st.expander("Methodology & data caveats"):
    st.markdown("""
- **Risk formula:** Overall = 0.40×News + 0.30×Logistics + 0.20×Commodity + 0.10×Weather (component scores 1–10).
- **Freight ETF (BDRY):** Equity ETF, not a direct freight rate index. Prefer news for logistics risk. Better indices: Freightos Baltic, Drewry WCI, SCFI.
- **Port congestion** not included (would require AIS/throughput data).
- **Commodity focus:** Oil and cotton are primary for consumer goods; copper for industrial context.
    """)

st.markdown(f'<div class="dashboard-footer">Viimeksi päivitetty: {ts}</div>', unsafe_allow_html=True)
