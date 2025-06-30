import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st.title("📊 AOC-Style Option Chain Viewer (NIFTY)")

ACCESS_TOKEN = st.secrets["upstox"]["token"]
INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"
st_autorefresh(interval=5000, key="refresh")

# 🔁 Fetch Expiries
@st.cache_data(ttl=300)
def get_expiries():
    url = f"https://api.upstox.com/v2/option/contract?instrument_key={INSTRUMENT_KEY}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json().get("data", [])
        return sorted({item["expiry"] for item in data})
    return []

# 📦 Fetch Option Chain
@st.cache_data(ttl=4)
def fetch_chain(expiry):
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={INSTRUMENT_KEY}&expiry_date={expiry}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json().get("data", [])
    return []

# 📊 Format helpers
def fmt(n): return f"{int(n):,}" if pd.notnull(n) else "-"
def percent(curr, prev):
    try: return "-" if prev == 0 else f"{((curr - prev) / prev) * 100:+.2f}%"
    except: return "-"
def oi_bar(val, maxval, color):
    width = min(val / maxval * 100, 100) if maxval else 0
    return f"<div style='background:#eee;height:6px;width:100%;'><div style='height:100%;background:{color};width:{width}%;'></div></div>"

def build_df(data):
    df = pd.DataFrame(data).dropna(subset=["call_options","put_options"])
    spot = df["underlying_spot_price"].iat[0]
    st.metric("📍 Spot Price", f"{spot:.2f}")
    df = df[(df.strike_price.between(spot-800, spot+800))].copy()

    def extract(opt, side):
        m = opt["market_data"]
        prev = m.get("prev_oi", 0)
        return pd.Series({
            f"{side}_ltp": m.get("ltp", 0),
            f"{side}_oi": m.get("oi", 0),
            f"{side}_oi_chg": m.get("oi", 0) - prev,
            f"{side}_oi_pct": percent(m.get("oi", 0), prev),
            f"{side}_volume": m.get("volume", 0),
            f"{side}_iv": opt.get("option_greeks", {}).get("iv", 0)
        })

    calls = df.call_options.apply(lambda x: extract(x, "call"))
    puts = df.put_options.apply(lambda x: extract(x, "put"))
    res = pd.concat([calls, df["strike_price"].rename("strike"), puts], axis=1)
    res["ATM"] = abs(res.strike - spot).eq(abs(res.strike - spot).min())
    return res, spot

def get_pcr(df):
    ce = df.call_oi.sum(); pe = df.put_oi.sum()
    pcr = round(pe / ce, 2) if ce else 0
    trend = "🔼 Bullish" if pcr > 1.1 else ("🔽 Bearish" if pcr < 0.9 else "🔁 Neutral")
    return pcr, trend

def render_table(df, exp, spot, pcr, trend):
    st.markdown(f"### Expiry: {exp} | PCR: {pcr} | Trend: {trend}")

    max_ce = df.call_oi.max(); max_pe = df.put_oi.max()
    top_ce_oi = sorted(df.call_oi, reverse=True)[:3]
    top_pe_oi = sorted(df.put_oi, reverse=True)[:3]
    top_ce_chg = sorted(df.call_oi_chg, reverse=True)[:3]
    top_pe_chg = sorted(df.put_oi_chg, reverse=True)[:3]
    top_ce_vol = sorted(df.call_volume, reverse=True)[:3]
    top_pe_vol = sorted(df.put_volume, reverse=True)[:3]

    def bg(val, top):
        return "#ff4d4d" if val == top[0] else ("#ffcc00" if val == top[1] else ("#fff176" if val == top[2] else ""))
    def bgp(val, top):
        return "#4CAF50" if val == top[0] else ("#ffcc00" if val == top[1] else ("#fff176" if val == top[2] else ""))

    st.markdown("""
    <style>
    table {font-family:Segoe UI;border-collapse:collapse;width:100%;font-size:13px;}
    th, td {border:1px solid #ddd;padding:6px;text-align:center;}
    th {position:sticky;top:0;background:#f0f0f0;z-index:1;}
    .atm {background:#fff9c4;font-weight:bold;}
    </style>
    """, unsafe_allow_html=True)

    html = "<div style='max-height:650px;overflow:auto'><table><tr>"
    cols = ["Call IV", "OI Chg", "Volume", "OI", "LTP", "Strike", "LTP", "OI", "Volume", "OI Chg", "Put IV"]
    html += "".join([f"<th>{col}</th>" for col in cols]) + "</tr>"

    for _, r in df.iterrows():
        atm = " class='atm'" if r.ATM else ""
        html += f"<tr{atm}>"
        html += f"<td>{r.call_iv:.2f}%</td>"
        html += f"<td style='background:{bg(r.call_oi_chg,top_ce_chg)}'>{fmt(r.call_oi_chg)}<br><small>{r.call_oi_pct}</small></td>"
        html += f"<td style='background:{bg(r.call_volume,top_ce_vol)}'>{fmt(r.call_volume)}<br><small>{percent(r.call_volume,0)}</small></td>"
        html += f"<td style='background:{bg(r.call_oi,top_ce_oi)}'>{fmt(r.call_oi)}{oi_bar(r.call_oi,max_ce,'#ff4d4d')}</td>"
        html += f"<td>{r.call_ltp:.2f}</td>"
        html += f"<td style='background:#f9f9f9'><b>{int(r.strike)}</b></td>"
        html += f"<td>{r.put_ltp:.2f}</td>"
        html += f"<td style='background:{bgp(r.put_oi,top_pe_oi)}'>{fmt(r.put_oi)}{oi_bar(r.put_oi,max_pe,'#4CAF50')}</td>"
        html += f"<td style='background:{bgp(r.put_volume,top_pe_vol)}'>{fmt(r.put_volume)}<br><small>{percent(r.put_volume,0)}</small></td>"
        html += f"<td style='background:{bgp(r.put_oi_chg,top_pe_chg)}'>{fmt(r.put_oi_chg)}<br><small>{r.put_oi_pct}</small></td>"
        html += f"<td>{r.put_iv:.2f}%</td>"
        html += "</tr>"
    html += "</table></div>"
    st.markdown(html, unsafe_allow_html=True)

# ▶️ MAIN
expiries = get_expiries()
if not expiries:
    st.error("❌ Expiries not loading")
else:
    expiry = st.selectbox("Select Expiry", expiries, index=0)
    data = fetch_chain(expiry)
    if not data:
        st.error("⚠️ No data for this expiry")
    else:
        df, spot = build_df(data)
        pcr, trend = get_pcr(df)
        render_table(df, expiry, spot, pcr, trend)