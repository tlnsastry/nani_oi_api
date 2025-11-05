from fastapi import FastAPI
import requests
from datetime import datetime

app = FastAPI(title="Nani OI API – Indices + Stock F&O Live Feed")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
    "Connection": "keep-alive",
}

def fetch_nse_option_chain(symbol: str, type_: str = "index"):
    """Fetch OI data for NSE index or stock."""
    base_url = "https://www.nseindia.com/api/option-chain-indices?symbol=" if type_ == "index" \
        else "https://www.nseindia.com/api/option-chain-equities?symbol="

    url = f"{base_url}{symbol}"
    session = requests.Session()
    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", {}).get("data", [])

        results = []
        for record in records:
            if "CE" in record and "PE" in record:
                ce = record["CE"]
                pe = record["PE"]
                oi_change = ce.get("changeinOpenInterest", 0) - pe.get("changeinOpenInterest", 0)
                signal = "BUY" if oi_change > 0 else "SELL"
                results.append({
                    "symbol": symbol,
                    "strikePrice": record.get("strikePrice"),
                    "oi_change": oi_change,
                    "price": ce.get("underlyingValue"),
                    "signal": signal
                })
        # Keep top 3 movers
        results = sorted(results, key=lambda x: abs(x["oi_change"]), reverse=True)[:3]
        return results
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return []

@app.get("/api/live_data")
def get_live_data():
    """Combine indices + selected stock OI data."""
    data = []

    # 1️⃣ Indices
    for sym in ["NIFTY", "BANKNIFTY"]:
        data.extend(fetch_nse_option_chain(sym, type_="index"))

    # 2️⃣ Stocks (you can add more below)
    stock_list = ["RELIANCE", "HDFCBANK", "TCS", "HAL", "ICICIBANK"]
    for stock in stock_list:
        data.extend(fetch_nse_option_chain(stock, type_="stock"))

    # 3️⃣ SENSEX (from BSE)
    try:
        sensex_resp = requests.get(
            "https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w?scripcode=1&flag=0",
            timeout=10
        )
        if sensex_resp.ok:
            js = sensex_resp.json()
            price = js.get("Data")[-1].get("value") if js.get("Data") else None
            data.append({"symbol": "SENSEX", "oi_change": 0, "price": price, "signal": "NEUTRAL"})
    except Exception:
        data.append({"symbol": "SENSEX", "oi_change": 0, "price": None, "signal": "NEUTRAL"})

    return data
