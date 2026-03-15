import json
import sys
from pathlib import Path
from data_fetchers import get_news, get_market_indicators, get_port_weather
from ai_analyzer import analyze_risk

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "latest_analysis.json"

def run(target_date=None):
    if target_date:
        print(f"Haetaan data päivälle {target_date}...")
    else:
        print("Haetaan reaaliaikainen data...")

    news       = get_news(target_date)
    indicators = get_market_indicators(target_date)
    weather    = get_port_weather(target_date)

    print(f"Data: {len(news)} uutista, {len(indicators)} indikaattoria, {len(weather)} satamaa")

    result = analyze_risk(news, indicators, weather)
    result["query_date"] = target_date or "realtime"

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Risk score: {result['overall_risk_score']}/10 ({result['risk_level']})")
    return result

if __name__ == "__main__":
    # Voi ajaa myös: python main.py 2024-03-15
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run(date_arg)
