import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Nani OI — Auto Signal Engine", layout="wide")
st.title("📊 Nani OI — Auto Signal Engine")
st.caption("Mock Data Mode (API 404 detected)")

# Mock sample OI data
data = [
    {"symbol": "NIFTY", "oi_change": 12000, "price": 24950, "signal": "BUY"},
    {"symbol": "BANKNIFTY", "oi_change": -8500, "price": 53220, "signal": "SELL"},
    {"symbol": "SENSEX", "oi_change": 7600, "price": 83300, "signal": "BUY"},
]

df = pd.DataFrame(data)

st.success("✅ Showing mock data (API 404 fallback)")
st.dataframe(df, use_container_width=True)

chart = px.bar(df, x="symbol", y="oi_change", color="signal", title="OI Change Trend")
st.plotly_chart(chart, use_container_width=True)
