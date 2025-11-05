import requests
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/live_data")
def get_live_data():
    try:
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
            "Connection": "keep-alive",
        }

        session = requests.Session()
        data = session.get(url, headers=headers, timeout=10).json()

        records = data["records"]["data"]
        total_oi_data = []

        for record in records:
            if "CE" in record and "PE" in record:
                ce = record["CE"]
                pe = record["PE"]
                oi_change = ce["changeinOpenInterest"] - pe["changeinOpenInterest"]
                signal = "BUY" if oi_change > 0 else "SELL"
                total_oi_data.append({
                    "symbol": "NIFTY",
                    "oi_change": oi_change,
                    "price": ce["underlyingValue"],
                    "signal": signal
                })

        # Only keep a few top OI movements
        total_oi_data = sorted(total_oi_data, key=lambda x: abs(x["oi_change"]), reverse=True)[:3]
        return total_oi_data

    except Exception as e:
        return {"error": str(e)}
