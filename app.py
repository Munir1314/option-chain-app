import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh
import math

# ✅ Streamlit setup
st.set_page_config(layout="wide")

# 🔐 Secure token from secrets
ACCESS_TOKEN = st.secrets["upstox"]["token"]

# 🔁 Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="refresh")

# 🚀 Fetch expiry list
@st.cache_data(ttl=60)
def fetch_expiries():
    url = "https://api.upstox.com/v2/option/expiries?instrument_key=NSE_INDEX|Nifty 50"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            expiries = res.json().get("data", [])
            return expiries
    except Exception as e:
        print("Error fetching expiries:", e)
    return []

# 🚀 Fetch option chain
@st.cache_data(ttl=4)
def fetch_chain(expiry):
    url = f"https://api.upstox.com/v2/option/chain?instrument_key=NSE_INDEX|Nifty 50&expiry_date={expiry}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("data", [])
    except Exception as e:
        print("Error fetching chain:", e)
    return []

# 🔧 Helpers
def fmt(n):
    try:
        return f"{int(n):,}"
    except:
        return "-"

def percent(curr, prev):
    try:
        if prev == 0: return ""
        pct = ((curr - prev) / prev) * 100
        return f"{pct:+.2f}%"
    except:
        return ""

def extract(option, side):
    m = option.get("market_data", {})
    g = option.get("option_greeks", {})
    oi = m.get("oi", 0)
    prev_oi = m.get("prev_oi", 0)
    volume = m.get("volume", 0)

    return pd.Series({
        f"{side}_ltp": m.get("ltp", 0.0),
        f"{side}_oi": oi,
        f"{side}_oi_chg": oi - prev_oi,
        f"{side}_oi_pct": percent(oi, prev_oi),
        f"{side}_volume": volume,
        f"{side}_iv": g.get("iv", None),
    })

def build_dataframe(data):
    df = pd.DataFrame(data)
    df = df[df['call_options'].notnull() & df['put_options'].notnull()]
    spot = df['underlying_spot_price'].iloc[0]
    df = df[(df['strike_price'] >= spot - 800) & (df['strike_price'] <= spot + 800)]

    calls = df["call_options"].apply(lambda x: extract(x, "call"))
    puts = df["put_options"].apply(lambda x: extract(x, "put"))
    strikes = df["strike_price"]

    full_df = pd.concat([calls, strikes.rename("strike"), puts], axis=1)
    return full_df, spot

def get_top3(df, col):
    return df.nlargest(3, col)[col].values

def render_table(df, expiry, spot):
    st.markdown("""
    <style>
    table {border-collapse: collapse; width: 100%;}
    th {position: sticky; top: 0; background: #f7f7f7; z-index: 2;}
    td, th {padding: 5px 8px; text-align: center; font-size: 14px;}
    </style>
    """, unsafe_allow_html=True)

    call_oi_top3 = get_top3(df, "call_oi")
    put_oi_top3 = get_top3(df, "put_oi")

    call_oi_chg_top3 = get_top3(df, "call_oi_chg")
    put_oi_chg_top3 = get_top3(df, "put_oi_chg")

    call_vol_top3 = get_top3(df, "call_volume")
    put_vol_top3 = get_top3(df, "put_volume")

    pcr = df["put_oi"].sum() / df["call_oi"].sum()
    trend = "📉 Bearish" if pcr < 0.9 else ("📈 Bullish" if pcr > 1.1 else "🔁 Neutral")

    st.markdown(f"""
    ### {spot:.2f}
    **Expiry:** `{expiry}` | **PCR:** `{pcr:.2f}` | **Trend:** {trend}
    """)

    headers = [
        "Call IV", "Call OI Chg", "Call Volume", "Call OI", "Call LTP",
        "Strike",
        "Put LTP", "Put OI", "Put Volume", "Put OI Chg", "Put IV"
    ]

    html = f"<table><tr>{''.join([f'<th>{col}</th>' for col in headers])}</tr>"

    for _, r in df.iterrows():
        strike_color = "background-color: #fff8dc;" if spot >= r.strike and spot <= r.strike + 50 else ""
        row = f"<tr style='{strike_color}'>"

        def cell(val, top3list, is_call, bar=False):
            bg = ""
            if val in top3list:
                idx = list(top3list).index(val)
                bg = ["#ff4d4d", "#ffc107", "#fff59d"] if is_call else ["#4CAF50", "#d4edda", "#f0fff0"][idx]
            bar_html = ""
            if bar:
                pct = min(100, (val / max(top3list)) * 100 if max(top3list) else 0)
                color = "red" if is_call else "green"
                bar_html = f"<div style='background:{color};width:{pct:.1f}%;height:5px;'></div>"
            return f"<td style='background:{bg}'>{fmt(val)}{bar_html}</td>"

        row += f"<td>{r.call_iv:.2f}%</td>"
        row += cell(r.call_oi_chg, call_oi_chg_top3, True)
        row += cell(r.call_volume, call_vol_top3, True)
        row += cell(r.call_oi, call_oi_top3, True, bar=True)
        row += f"<td>{r.call_ltp:.2f}</td>"

        row += f"<td><b>{int(r.strike)}</b></td>"

        row += f"<td>{r.put_ltp:.2f}</td>"
        row += cell(r.put_oi, put_oi_top3, False, bar=True)
        row += cell(r.put_volume, put_vol_top3, False)
        row += cell(r.put_oi_chg, put_oi_chg_top3, False)
        row += f"<td>{r.put_iv:.2f}%</td>"

        row += "</tr>"
        html += row

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# ▶️ Main
expiries = fetch_expiries()
if not expiries:
    st.error("❌ Unable to fetch expiries. Check your API token or internet connection.")
else:
    expiry = st.selectbox("Choose Expiry", expiries, index=0)
    data = fetch_chain(expiry)
    if not data:
        st.error("⚠️ Failed to fetch option chain data")
    else:
        df, spot = build_dataframe(data)
        render_table(df, expiry, spot)
