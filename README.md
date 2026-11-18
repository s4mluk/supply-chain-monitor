# Supply Chain Risk Monitor

Supply chain risk dashboard for consumer goods companies with significant Asia sourcing exposure. Aggregates news, market indicators, and port weather into a weighted risk score with an executive summary and recommended actions.

<!-- TODO: add a dashboard screenshot (docs/dashboard.png) after one real run, then embed it here: ![Dashboard](docs/dashboard.png) -->

## Features

- **Weighted risk scoring:** Overall = 0.40×News + 0.30×Logistics + 0.20×Commodity + 0.10×Weather (transparent formula)
- **Data sources:** News (LSEG/Refinitiv), market indicators (yfinance: freight proxy, oil, cotton, copper, USD/CNY), port weather (Open-Meteo)
- **Modes:** Real-time or historical analysis by date
- **Output:** Executive summary, top risk drivers, recommended actions, port-level weather risk, key assumptions, and data limitations

## Prerequisites

- Python 3.10+
- **OpenAI API key** (required for risk analysis)
- **LSEG/Refinitiv** session (optional; for news. Without it, news list may be empty; indicators and weather still run.)

## Installation

```bash
git clone https://github.com/s4mluk/supply-chain-monitor.git
cd supply-chain-monitor
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root (see `.env.example`):

```env
OPENAI_API_KEY=sk-...
```

For news: configure LSEG/Refinitiv as required by the `lseg-data` package (e.g. desktop session or credentials).

## Usage

**Run analysis (writes `latest_analysis.json`):**

```bash
# Real-time (last 48h news, latest indicators and weather)
python main.py

# Historical (specific date)
python main.py 2024-03-25
```

**Start dashboard:**

```bash
streamlit run dashboard.py
```

Open the URL shown (e.g. http://localhost:8501). Use the sidebar to switch between real-time and historical mode and to run a new analysis.

## Project structure

```
.
├── main.py           # Entry: fetch data + run AI analysis
├── data_fetchers.py  # News (LSEG), indicators (yfinance), port weather (Open-Meteo)
├── ai_analyzer.py    # OpenAI-based risk synthesis and scoring
├── dashboard.py      # Streamlit UI
├── latest_analysis.json  # Output (created after first run)
├── requirements.txt
├── .env              # Not in repo; copy from .env.example
└── .streamlit/
    └── config.toml   # Streamlit theme
```

## Methodology

- **Risk formula:** Component scores (1–10) are produced by the model from headlines, indicators, and port weather. Overall score is computed as 0.40×News + 0.30×Logistics + 0.20×Commodity + 0.10×Weather and mapped to LOW / MEDIUM / HIGH / CRITICAL.
- **Freight:** The app uses a freight ETF (BDRY) as a proxy only; it is not a direct freight rate index. Prefer news (e.g. Suez, port disruptions) for logistics risk. Better indices: Freightos Baltic, Drewry WCI, SCFI.
- **Port congestion** (ships waiting, AIS, throughput) is not included.

## License

MIT. See [LICENSE](LICENSE).
