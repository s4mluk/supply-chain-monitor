import lseg.data as ld
import yfinance as yf
import requests
from datetime import timedelta, datetime, date

ld.open_session()

# ================================
# 1. UUTISET — Refinitiv
# ================================
NEWS_PER_QUERY = 18   # per teemahaku (enemmän = parempi kattavuus, enemmän tokeneja)
NEWS_MAX_TOTAL = 45   # max uutista analyysiin (riittää syvemmälle kuvaan)

def get_news(target_date=None):
    # Jos päivämäärä annettu, hae sen ympäriltä
    # Muuten viimeiset 48h
    if target_date:
        start = f"{target_date}T00:00:00"
        end   = f"{target_date}T23:59:59"
    else:
        start = timedelta(days=-2)
        end   = timedelta(days=0)

    queries = [
        "Asia shipping OR China port OR Suez Canal OR Red Sea disruption",
        "freight rates OR container shortage OR supply chain disruption",
        "consumer goods supply chain OR FMCG logistics OR retail inventory",
        "port congestion OR dock strike OR shipping delay OR logistics bottleneck",
    ]

    all_results = []
    seen_ids    = set()

    for query in queries:
        try:
            headlines = ld.news.get_headlines(
                query=query,
                start=start,
                end=end,
                count=NEWS_PER_QUERY
            )

            for idx, row in headlines.iterrows():
                if row["sourceCode"] in ["NS:TWIT", "NS:TWTR"]:
                    continue
                if row["headline"].startswith("@"):
                    continue
                if row["storyId"] in seen_ids:
                    continue

                seen_ids.add(row["storyId"])
                all_results.append({
                    "headline": row["headline"],
                    "date":     str(idx),
                    "storyId":  row["storyId"],
                    "category": query.split(" OR ")[0]
                })
        except Exception as e:
            print(f"Virhe haussa '{query}': {e}")

    return all_results[:NEWS_MAX_TOTAL]

# ================================
# 2. MARKKINAINDIKAATTORIT — yfinance
# BDRY = osake-ETF, EI suora freight rate; paremmat: Freightos Baltic, Drewry WCI, SCFI
# Consumer goods: öljy, puuvilla, pakkaus tärkeämpiä kuin kupari
# ================================
def get_market_indicators(target_date=None):
    tickers = {
        "Freight ETF (BDRY, proxy only)": "BDRY",
        "Crude Oil (WTI)":                 "CL=F",
        "Cotton (consumer goods)":         "CT=F",
        "Copper":                         "HG=F",
        "USD/CNY (Aasia-kustannukset)":   "CNY=X",
    }

    results = []
    for name, ticker in tickers.items():
        try:
            if target_date:
                end_dt   = datetime.strptime(target_date, "%Y-%m-%d")
                start_dt = end_dt - timedelta(days=30)
                hist = yf.Ticker(ticker).history(
                    start=start_dt.strftime("%Y-%m-%d"),
                    end=end_dt.strftime("%Y-%m-%d")
                )
            else:
                hist = yf.Ticker(ticker).history(period="1mo")

            if hist.empty or len(hist) < 2:
                print(f"Ei dataa: {name}")
                continue

            latest = hist["Close"].iloc[-1]
            prev_5 = hist["Close"].iloc[-min(6, len(hist))] if len(hist) >= 5 else hist["Close"].iloc[0]
            prev_30 = hist["Close"].iloc[0]
            change_5d = ((latest - prev_5) / prev_5) * 100
            change_30d = ((latest - prev_30) / prev_30) * 100

            results.append({
                "indicator": name,
                "price":     round(float(latest), 2),
                "change_5d": round(float(change_5d), 2),
                "change_30d": round(float(change_30d), 2),
            })
        except Exception as e:
            print(f"Virhe {name}: {e}")

    return results

# ================================
# 3. SATAMASÄÄ — Open-Meteo
# ================================
def get_port_weather(target_date=None):
    ports = {
        "Singapore":   (1.29,  103.85),
        "Rotterdam":   (51.96,  4.13),
        "Shanghai":    (31.23, 121.47),
        "Los Angeles": (33.74, -118.27)
    }

    results = {}
    for port, (lat, lon) in ports.items():
        try:
            if target_date:
                # Historiallinen sää Open-Meteosta
                r = requests.get(
                    "https://archive-api.open-meteo.com/v1/archive",
                    params={
                        "latitude":        lat,
                        "longitude":       lon,
                        "start_date":      target_date,
                        "end_date":        target_date,
                        "daily":           "wind_speed_10m_max",
                        "wind_speed_unit": "ms"
                    }
                ).json()
                wind = r["daily"]["wind_speed_10m_max"][0]
            else:
                r = requests.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude":        lat,
                        "longitude":       lon,
                        "current":         "wind_speed_10m,weather_code",
                        "wind_speed_unit": "ms"
                    }
                ).json()
                wind = r["current"]["wind_speed_10m"]

            # Sääkoodi (WMO) reaaliaikassa
            weather_code = r.get("current", {}).get("weather_code", 0) if not target_date else None
            results[port] = {
                "wind_speed_ms": round(wind, 2),
                "alert":         wind > 15,
                "weather_code":  weather_code,
            }
        except Exception as e:
            print(f"Virhe {port}: {e}")

    return results