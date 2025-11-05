from fastapi import FastAPI
import requests
import numpy as np

app = FastAPI(title="Nani OI API – Accuracy Engine (Signal Strength Model)")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
    "Connection": "keep-alive",
}

def fetch_nse_option_chain(symbol: str, type_: str = "index"):
    """Fetch OI + price data and compute signal strength."""
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
                price = ce.get("underlyingValue")
                signal = "BUY" if oi_change > 0 else "SELL"

                # --- Compute signal strength ---
                normalized_oi = np.tanh(oi_change / 50000)  # smooth out extreme spikes
                price_change = ce.get("lastPrice", 0) - pe.get("lastPrice", 0)
                normalized_price = np.tanh(price_change / 100)
                iv_shift = (ce.get("impliedVolatility", 0) - pe.get("impliedVolatility", 0)) / 100

                signal_strength = round((normalized_oi * 0.6) + (normalized_price * 0.3) + (iv_shift * 0.1), 2)

                results.append({
                    "symbol": symbol,
                    "strikePrice": record.get("strikePrice"),
                    "oi_change": oi_change,
                    "price": price,
                    "signal": signal,
                    "signal_strength": signal_strength
                })

        # Keep only top 3 signals by strength
        results = sorted(results, key=lambda x: abs(x["signal_strength"]), reverse=True)[:3]
        return results

    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return []


@app.get("/api/live_data")
def get_live_data():
    """Combine index + stock data with computed accuracy."""
    data = []

    # Indices
    for sym in ["NIFTY", "BANKNIFTY"]:
        data.extend(fetch_nse_option_chain(sym, type_="index"))

    # Stocks
    stock_list = ["RELIANCE", "HDFCBANK", "TCS", "HAL", "ICICIBANK"]
    for stock in stock_list:
        data.extend(fetch_nse_option_chain(stock, type_="stock"))

    # Sensex (from BSE)
    try:
        sensex_resp = requests.get(
            "https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w?scripcode=1&flag=0",
            timeout=10
        )
        if sensex_resp.ok:
            js = sensex_resp.json()
            price = js.get("Data")[-1].get("value") if js.get("Data") else None
            data.append({
                "symbol": "SENSEX",
                "oi_change": 0,
                "price": price,
                "signal": "NEUTRAL",
                "signal_strength": 0.0
            })
    except Exception:
        data.append({"symbol": "SENSEX", "oi_change": 0, "price": None, "signal": "NEUTRAL", "signal_strength": 0.0})

    return data
