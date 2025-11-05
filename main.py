# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Nani OI API", version="1.0")

# allow all origins so Streamlit dashboard can access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/live_data")
def get_live_data():
    # later you'll fetch from your DB or Nani OI engine
    data = [
        {"symbol": "NIFTY", "oi_change": 15200, "price": 24925, "signal": "BUY"},
        {"symbol": "BANKNIFTY", "oi_change": -9800, "price": 53310, "signal": "SELL"},
        {"symbol": "SENSEX", "oi_change": 7100, "price": 83350, "signal": "BUY"},
    ]
    return JSONResponse(content=data)
