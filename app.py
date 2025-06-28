import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st.title("📊 Live Option Chain - NIFTY")

ACCESS_TOKEN = st.secrets["upstox"]["token"]
INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"
EXPIRY_DATE = "2025-07-04"  # You can change it later dynamically
STRIKE_RANGE = st.slider("Strike Range (+/- from ATM)", 5, 30, 10)

def fetch_option_chain():
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={INSTRUMENT_KEY}&expiry_date={EXPIRY_DATE}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        st.error("Failed to fetch data")
        return []

def build_dataframe(chain_data):
    df = pd.DataFrame(chain_data)
    df = df[(df['call_options'].notnull()) & (df['put_options'].notnull())]

    atm = df['underlying_spot_price'].iloc[0]
    df = df[(df['strike_price'] >= atm - STRIKE_RANGE * 50) & (df['strike_price'] <= atm + STRIKE_RANGE * 50)]

    def extract_data(option, side):
        if not option or not option.get("market_data"):
            return {}
        data = option["market_data"]
        greeks = option.get("option_greeks", {})
        return {
            f"{side}_ltp": data.get("ltp", 0),
            f"{side}_oi": data.get("oi", 0),
            f"{side}_volume": data.get("volume", 0),
            f"{side}_oi_chg": data.get("oi", 0) - data.get("prev_oi", 0),
            f"{side}_iv": greeks.get("iv", 0),
        }

    calls = df["call_options"].apply(lambda x: extract_data(x, "call"))
    puts = df["put_options"].apply(lambda x: extract_data(x, "put"))

    call_df = pd.DataFrame(calls.tolist())
    put_df = pd.DataFrame(puts.tolist())

    final_df = pd.concat([call_df, df["strike_price"], put_df], axis=1)

    return final_df.sort_values("strike_price")

def highlight_support_resistance(df, side):
    for col in [f"{side}_oi", f"{side}_volume", f"{side}_oi_chg"]:
        top3 = df[col].nlargest(3).index
        for idx, color in zip(top3, ["red", "orange", "yellow"] if side == "call" else ["green", "yellowgreen", "lightyellow"]):
            df.at[idx, f"{side}_highlight"] = color
    return df

def apply_colors(row, col, side):
    return f"background-color: {row.get(f'{side}_highlight', '')}" if col.startswith(f"{side}_") else ""

def render():
    chain = fetch_option_chain()
    if not chain:
        st.warning("No data received")
        return

    df = build_dataframe(chain)
    df = highlight_support_resistance(df, "call")
    df = highlight_support_resistance(df, "put")

    style = df.style.applymap(lambda v: "", subset=["strike_price"])
    for side in ["call", "put"]:
        for col in df.columns:
            style = style.apply(lambda row: apply_colors(row, col, side), axis=1, subset=[col])

    st.dataframe(style, use_container_width=True)

# ✅ Correct way using streamlit_autorefresh
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="datarefresh")

# Then call the render function
render()
