import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


st.set_page_config(page_title="S&P 500 Tracker", layout="wide")
st.title("📈 S&P 500 Tracker")
st.caption("Data from Yahoo Finance (ticker ^GSPC). Prices may be delayed.")




# Cache for an hour so the app doesn't call Yahoo on every click.
@st.cache_data(ttl=3600, show_spinner="Loading data from Yahoo Finance...")
def load_data(period):
    df = yf.Ticker("^GSPC").history(period=period, auto_adjust=False)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df




# ---- Sidebar controls ----
st.sidebar.header("Settings")
period_label = st.sidebar.selectbox(
    "Time range",
    ["1 month", "6 months", "Year to date", "1 year", "5 years", "Max"],
    index=3,
)
period = {"1 month": "1mo", "6 months": "6mo", "Year to date": "ytd",
          "1 year": "1y", "5 years": "5y", "Max": "max"}[period_label]
chart_type = st.sidebar.radio("Chart type", ["Line", "Candlestick"])
show_ma50 = st.sidebar.checkbox("50-day moving average", value=True)
show_ma200 = st.sidebar.checkbox("200-day moving average", value=False)


# ---- Data ----
try:
    df = load_data(period)
except Exception as e:
    st.error(f"Could not load data from Yahoo Finance: {e}")
    st.stop()


if df.empty:
    st.error("Yahoo Finance returned no data. Try again in a minute.")
    st.stop()


df["MA50"] = df["Close"].rolling(50).mean()
df["MA200"] = df["Close"].rolling(200).mean()


# ---- Summary numbers ----
last, prev, first = df["Close"].iloc[-1], df["Close"].iloc[-2], df["Close"].iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest close", f"{last:,.2f}", f"{(last / prev - 1) * 100:+.2f}% today")
c2.metric(f"Change over {period_label.lower()}", f"{(last / first - 1) * 100:+.2f}%")
c3.metric("High in range", f"{df['High'].max():,.2f}")
c4.metric("Low in range", f"{df['Low'].min():,.2f}")


# ---- Chart ----
fig = go.Figure()
if chart_type == "Candlestick":
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"],
                                 low=df["Low"], close=df["Close"], name="S&P 500"))
else:
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(width=2)))
if show_ma50:
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="50-day MA", line=dict(width=1.5)))
if show_ma200:
    fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], name="200-day MA", line=dict(width=1.5)))
fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10),
                  xaxis_rangeslider_visible=False, hovermode="x unified",
                  yaxis_title="Index level", legend=dict(orientation="h", y=1.05))
st.plotly_chart(fig, width="stretch")


st.caption("Note: moving averages need 50 or 200 trading days of data, so they don't appear on short ranges.")


# ---- Raw data ----
with st.expander("Show data table"):
    table = df[["Open", "High", "Low", "Close", "Volume"]].sort_index(ascending=False)
    st.dataframe(table.style.format("{:,.2f}", subset=["Open", "High", "Low", "Close"]))
    st.download_button("Download as CSV", table.to_csv().encode(), "sp500.csv", "text/csv")
