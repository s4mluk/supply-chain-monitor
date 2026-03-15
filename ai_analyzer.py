from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY not set. Add it to .env (see .env.example). Do not commit .env.")
client = OpenAI(api_key=_api_key)

# Painotetut riskiscoret — näytetään dashboardissa (analytiikkatason läpinäkyvyys)
RISK_WEIGHTS = {
    "news_risk":      0.40,
    "logistics_risk": 0.30,
    "commodity_risk": 0.20,
    "weather_risk":   0.10,
}

def _compute_overall(signal_breakdown):
    total = sum(
        signal_breakdown.get(k, 5) * v
        for k, v in RISK_WEIGHTS.items()
    )
    score = max(1, min(10, round(total)))
    if score <= 3:
        level = "LOW"
    elif score <= 5:
        level = "MEDIUM"
    elif score <= 8:
        level = "HIGH"
    else:
        level = "CRITICAL"
    return score, level

def analyze_risk(news, indicators, weather):
    
    news_text = "\n".join([
        f"[{item['category']}] {item['date'][:10]} — {item['headline']}"
        for item in news
    ])
    
    indicators_text = "\n".join([
        f"{item['indicator']}: {item['price']} — 5pv: {item['change_5d']:+.1f}%, 30pv: {item.get('change_30d', item['change_5d']):+.1f}%"
        for item in indicators
    ])
    
    def _weather_line(port, data):
        line = f"{port}: {data['wind_speed_ms']} m/s {'ALERT' if data['alert'] else 'normal'}"
        if data.get("weather_code") is not None:
            line += f" (sääkoodi {data['weather_code']})"
        return line
    weather_text = "\n".join([_weather_line(port, d) for port, d in weather.items()])
    
    prompt = f"""
Olet supply chain -riskianalyytikko. Asiakas: eurooppalainen consumer goods -yritys (Aasia-sourcing).

TÄRKEÄÄ DATAN RAKENTEESTA:
- "Freight ETF (BDRY)" on osake-ETF, EI suora freight rate -indeksi. ETF-liike voi olla päinvastainen kuin todelliset konttihinnat (esim. 2021 konttipula vs. BDRY). Käytä logistiikkariskissä ensisijaisesti UUTISIA (Suez, satamat, ruuhkat).
- Consumer goods -raaka-aineet: öljy, puuvilla, muovit, pakkaus ovat tärkeämpiä kuin kupari (kupari enemmän teollisuus/rakentaminen). Arvioi commodity_risk öljyn ja muiden consumer-relevanttien signaalien mukaan.
- Executive summary: sisällytä KONKREETTISET LUVUT kun mahdollista (esim. "noin 12 % maailmankaupasta kulkee Suezin kautta", "yli 200 alusta jonossa", "kiertoreitti Afrikan ympäri +2 viikkoa").

Analysoi signaalit ja anna VAIN komponenttiscoret 1–10. Kokonaisriski lasketaan automaattisesti kaavalla:
Overall = 0.40×news_risk + 0.30×logistics_risk + 0.20×commodity_risk + 0.10×weather_risk

=== UUTISET ===
{news_text}

=== MARKKINAINDIKAATTORIT ===
{indicators_text}

=== SATAMASÄÄ ===
{weather_text}

=== OHJE ===
Palauta AINOASTAAN validi JSON ilman markdownia.
Älä laske overall_risk_score tai risk_level — ne lasketaan kaavasta.

{{
  "top_risk_drivers": [
    {{ "driver": "<nimi>", "severity": "LOW|MEDIUM|HIGH", "explanation": "<yksi lause, viittaa dataan>" }},
    {{ "driver": "<nimi>", "severity": "LOW|MEDIUM|HIGH", "explanation": "<yksi lause>" }},
    {{ "driver": "<nimi>", "severity": "LOW|MEDIUM|HIGH", "explanation": "<yksi lause>" }}
  ],
  "executive_summary": "<2-3 lausetta, sisällytä konkreettiset luvut jos uutisissa mainitaan>",
  "recommended_actions": ["<toimenpide 1>", "<toimenpide 2>", "<toimenpide 3>"],
  "signal_breakdown": {{
    "news_risk":      <1-10 kokonaisluku>,
    "logistics_risk": <1-10>,
    "commodity_risk": <1-10>,
    "weather_risk":   <1-10>
  }},
  "port_weather_risk": {{
    "Singapore": "low|medium|high",
    "Rotterdam": "low|medium|high",
    "Shanghai": "low|medium|high",
    "Los Angeles": "low|medium|high"
  }},
  "key_assumptions": ["<oletus 1>", "<oletus 2>"],
  "data_limitations": "<Lyhyt kappale. Mainitse: (1) BDRY on ETF, ei freight rate -indeksi; paremmat mittarit olisivat Freightos Baltic, Drewry WCI, SCFI. (2) Port congestion (alusten odotus, AIS, throughput) ei ole mukana.>",
  "timestamp": "{datetime.now().isoformat()}"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    raw = response.choices[0].message.content
    raw = raw.replace("```json", "").replace("```", "").strip()
    result = json.loads(raw)

    # Kokonaisriski lasketaan painotetusta kaavasta (ei AI-arvio)
    sb = result.get("signal_breakdown", {})
    overall_score, risk_level = _compute_overall(sb)
    result["overall_risk_score"] = overall_score
    result["risk_level"] = risk_level
    result["scoring_formula"] = "0.40×News + 0.30×Logistics + 0.20×Commodity + 0.10×Weather"
    return result


# ================================
# TESTI
# ================================
if __name__ == "__main__":
    # Testitiedot ilman oikeaa dataa
    test_news = [
        {"category": "Asia shipping", "date": "2026-03-15", "headline": "Red Sea disruptions continue to affect container shipping rates"},
        {"category": "freight rates", "date": "2026-03-15", "headline": "Container shortage worsening in Asian ports"},
        {"category": "consumer goods", "date": "2026-03-15", "headline": "FMCG companies warning of supply chain cost increases"}
    ]
    test_indicators = [
        {"indicator": "Freight ETF (BDI proxy)", "price": 4.21,  "change_5d": -8.3},
        {"indicator": "Crude Oil (WTI)",          "price": 98.71, "change_5d": 18.3},
        {"indicator": "Copper",                   "price": 5.76,  "change_5d": -2.5}
    ]
    test_weather = {
        "Singapore":   {"wind_speed_ms": 1.22, "alert": False},
        "Rotterdam":   {"wind_speed_ms": 6.80, "alert": False},
        "Shanghai":    {"wind_speed_ms": 1.36, "alert": False},
        "Los Angeles": {"wind_speed_ms": 1.77, "alert": False}
    }
    
    print("Ajetaan analyysi...")
    result = analyze_risk(test_news, test_indicators, test_weather)
    
    print(f"\nRiskiscore: {result['overall_risk_score']}/10 ({result['risk_level']})")
    print(f"\nExecutive summary:\n{result['executive_summary']}")
    print(f"\nTop riskit:")
    for driver in result['top_risk_drivers']:
        print(f"  {driver['severity']} — {driver['driver']}: {driver['explanation']}")
    print(f"\nSuositukset:")
    for action in result['recommended_actions']:
        print(f"  → {action}")
