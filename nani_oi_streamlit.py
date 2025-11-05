import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from config import NANI_OI_API_URL, API_HEADERS

# ──────────────────────────────────────────────
# Streamlit Page Setup
# ──────────────────────────────────────────────
st.set_page_config(page_title="Nani OI — Auto Signal Engine", layout="wide")
st.title("📊 Nani OI — Auto Signal Engine")
st.caption("Live OI + AI Signal Dashboard powered by Nani OI API")

# Sidebar Controls
st.sidebar.header("⚙️ Dashboard Controls")

refresh_rate = 30  # seconds
auto_refresh = st.sidebar.checkbox("🔁 Auto-refresh every 30s", value=True)

index_filter = st.sidebar.selectbox(
    "Select Index",
    options=["ALL", "NIFTY", "BANKNIFTY", "SENSEX"],
    index=0
)

if st.sidebar.button("🔄 Refresh Now"):
    st.rerun()

st.info(f"🔄 Fetching live data from API: {NANI_OI_API_URL}")

# ──────────────────────────────────────────────
# Local session state for timeline tracking
# ──────────────────────────────────────────────
if "timeline" not in st.session_state:
    st.session_state.timeline = pd.DataFrame(columns=["time", "buy_signals", "sell_signals"])

# ──────────────────────────────────────────────
# Fetch & Display Data
# ──────────────────────────────────────────────
try:
    response = requests.get(NANI_OI_API_URL, headers=API_HEADERS, timeout=10)

    if response.status_code == 200:
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df.columns = [c.lower().strip() for c in df.columns]

            # Apply index filter
            if index_filter != "ALL" and "symbol" in df.columns:
                df = df[df["symbol"].str.contains(index_filter, case=False, na=False)]

            # Format BUY/SELL signals
            def format_signal(signal):
                s = str(signal).upper()
                if s == "BUY":
                    return "🟢 BUY"
                elif s == "SELL":
                    return "🔴 SELL"
                else:
                    return "⚪ NEUTRAL"

            if "signal" in df.columns:
                df["Signal"] = df["signal"].apply(format_signal)

            # ──────────────────────────────────────────────
            # AI Market Bias & Sentiment Calculation
            # ──────────────────────────────────────────────
            total_signals = len(df)
            buy_count = len(df[df["signal"].str.upper() == "BUY"])
            sell_count = len(df[df["signal"].str.upper() == "SELL"])

            bullish_pct = round((buy_count / total_signals) * 100, 1) if total_signals else 0
            bearish_pct = round((sell_count / total_signals) * 100, 1) if total_signals else 0

            # Determine sentiment level
            sentiment_score = bullish_pct - bearish_pct
            if sentiment_score > 50:
                sentiment_label = "🟢 Strong Bullish"
                sentiment_color = "#16a34a"
            elif 20 < sentiment_score <= 50:
                sentiment_label = "🟢 Mild Bullish"
                sentiment_color = "#4ade80"
            elif -20 <= sentiment_score <= 20:
                sentiment_label = "🟡 Neutral"
                sentiment_color = "#facc15"
            elif -50 <= sentiment_score < -20:
                sentiment_label = "🔴 Mild Bearish"
                sentiment_color = "#f87171"
            else:
                sentiment_label = "🔴 Strong Bearish"
                sentiment_color = "#dc2626"

            # Display Sentiment Gauge
            st.markdown("---")
            st.subheader("🧠 AI Sentiment Gauge (Market Mood)")
            st.markdown(
                f"""
                <div style="background-color:#f1f5f9;padding:15px;border-radius:10px;">
                    <div style="font-size:20px;color:{sentiment_color};font-weight:bold;">{sentiment_label}</div>
                    <div style="background-color:#e5e7eb;border-radius:8px;height:18px;width:100%;margin-top:8px;">
                        <div style="background-color:{sentiment_color};height:18px;width:{abs(sentiment_score)}%;border-radius:8px;"></div>
                    </div>
                    <p style="margin-top:5px;color:#444;">Bullish: {bullish_pct}% | Bearish: {bearish_pct}%</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Update timeline data
            new_entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "buy_signals": buy_count,
                "sell_signals": sell_count
            }
            st.session_state.timeline = pd.concat(
                [st.session_state.timeline, pd.DataFrame([new_entry])],
                ignore_index=True
            )

            # Bias summary cards
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🐂 Bullish Bias", f"{bullish_pct}%", delta=f"{buy_count} BUY Signals")
            with col2:
                st.metric("🐻 Bearish Bias", f"{bearish_pct}%", delta=f"{sell_count} SELL Signals")

            # ──────────────────────────────────────────────
            # Top Gainers / Losers Panel (Visual Bars)
            # ──────────────────────────────────────────────
            st.markdown("---")
            st.subheader("📊 Top OI Gainers & Losers")

            if "oi_change" in df.columns and "symbol" in df.columns:
                # Calculate absolute OI range for scaling bars
                oi_min = df["oi_change"].min()
                oi_max = df["oi_change"].max()
                oi_range = max(abs(oi_min), abs(oi_max))

                top_gainers = df.sort_values("oi_change", ascending=False).head(3)
                top_losers = df.sort_values("oi_change", ascending=True).head(3)

                col_g, col_l = st.columns(2)
                with col_g:
                    st.markdown("### 📈 Top Gainers")
                    for _, row in top_gainers.iterrows():
                        width = int((abs(row["oi_change"]) / oi_range) * 100)
                        st.markdown(
                            f"""
                            <div style="margin-bottom:8px;">
                                <b style="color:green;">🟢 {row['symbol']}</b> — +{row['oi_change']} OI
                                <div style="background-color:#e6ffe6;border-radius:8px;height:12px;width:100%;">
                                    <div style="background-color:#00b300;height:12px;width:{width}%;border-radius:8px;"></div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                with col_l:
                    st.markdown("### 📉 Top Losers")
                    for _, row in top_losers.iterrows():
                        width = int((abs(row["oi_change"]) / oi_range) * 100)
                        st.markdown(
                            f"""
                            <div style="margin-bottom:8px;">
                                <b style="color:red;">🔴 {row['symbol']}</b> — {row['oi_change']} OI
                                <div style="background-color:#ffe6e6;border-radius:8px;height:12px;width:100%;">
                                    <div style="background-color:#cc0000;height:12px;width:{width}%;border-radius:8px;"></div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # ──────────────────────────────────────────────
            # Display Table
            # ──────────────────────────────────────────────
            st.success(f"✅ Live data received successfully! ({len(df)} records)")
            st.dataframe(df, use_container_width=True)

            # ──────────────────────────────────────────────
            # OI vs Price Chart
            # ──────────────────────────────────────────────
            if "price" in df.columns and "oi_change" in df.columns:
                st.subheader("📈 OI Change vs Price Trend")
                chart = px.scatter(
                    df,
                    x="price",
                    y="oi_change",
                    color="signal" if "signal" in df.columns else None,
                    hover_data=["symbol"] if "symbol" in df.columns else None,
                    title="OI Movement vs Price"
                )
                st.plotly_chart(chart, use_container_width=True)

            # ──────────────────────────────────────────────
            # Signal Timeline Chart
            # ──────────────────────────────────────────────
            st.markdown("---")
            st.subheader("🕒 Signal Timeline (Buy vs Sell Trend)")

            timeline_df = st.session_state.timeline.tail(20)
            if not timeline_df.empty:
                fig_timeline = px.line(
                    timeline_df,
                    x="time",
                    y=["buy_signals", "sell_signals"],
                    markers=True,
                    title="Intraday Signal Momentum",
                    labels={"value": "Signal Count", "time": "Time"},
                )
                st.plotly_chart(fig_timeline, use_container_width=True)

        else:
            st.warning("⚠️ API returned no valid data or empty response.")
    else:
        st.error(f"⚠️ API error: {response.status_code} — {response.text[:200]}")

except Exception as e:
    st.error(f"❌ Failed to connect to API: {e}")

# ──────────────────────────────────────────────
# Auto Refresh Logic
# ──────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
