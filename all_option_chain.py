import requests
import pandas as pd

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyTkNTVTUiLCJqdGkiOiI2ODVmZmMyMDk2ZDE4ODdiMjFmYzI0NDgiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzUxMTIwOTI4LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTExNDgwMDB9.E07aDE8ci9ZSMVGFBecJ0j5aObVABS34nFdRrxPLa-g"

EXPIRY_MAP = {
    "NIFTY": ("NSE_INDEX|Nifty 50", "2025-07-03"),
    "BANKNIFTY": ("NSE_INDEX|Bank Nifty", "2025-07-31"),
    "FINNIFTY": ("NSE_INDEX|Fin Nifty", "2025-07-31"),
    "MIDCPNIFTY": ("NSE_INDEX|Midcap Nifty", "2025-07-31")
}

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def fetch_option_chain(index_name, instrument_key, expiry):
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry}"
    response = requests.get(url, headers=headers)

    try:
        data = response.json()
    except Exception as e:
        print(f"[ERROR] JSON decoding failed for {index_name}: {e}")
        print("Raw response:", response.text)
        return None

    # ✅ Fix: data["data"] is a list of option chain entries
    if not isinstance(data, dict) or "data" not in data:
        print(f"[ERROR] Unexpected format for {index_name}")
        print(data)
        return None

    chain_data = data["data"]
    if not isinstance(chain_data, list) or not chain_data:
        print(f"[SKIPPED] No option chain data for {index_name}")
        return None

    records = []
    for entry in chain_data:
        ce = entry.get("call_options", {})
        pe = entry.get("put_options", {})

        ce_market = ce.get("market_data", {})
        pe_market = pe.get("market_data", {})
        ce_iv = ce.get("option_greeks", {}).get("iv", 0)
        pe_iv = pe.get("option_greeks", {}).get("iv", 0)

        ce_oi = ce_market.get("oi", 0)
        pe_oi = pe_market.get("oi", 0)
        pcr = round(pe_oi / ce_oi, 2) if ce_oi else None

        records.append({
            "Index": index_name,
            "Expiry": entry.get("expiry", expiry),
            "Strike": entry.get("strike_price", 0),
            "CE OI": ce_oi,
            "CE COI": ce_market.get("oi", 0) - ce_market.get("prev_oi", 0),
            "CE LTP": ce_market.get("ltp", 0),
            "CE IV": ce_iv,
            "PE OI": pe_oi,
            "PE COI": pe_market.get("oi", 0) - pe_market.get("prev_oi", 0),
            "PE LTP": pe_market.get("ltp", 0),
            "PE IV": pe_iv,
            "PCR": pcr
        })

    return pd.DataFrame(records)

# 🔁 Loop
all_data = []
for index_name, (instrument_key, expiry) in EXPIRY_MAP.items():
    print(f"📥 Fetching {index_name}...")
    df = fetch_option_chain(index_name, instrument_key, expiry)
    if df is not None:
        all_data.append(df)

# 💾 Save to Excel
if all_data:
    final_df = pd.concat(all_data).sort_values(["Index", "Strike"]).reset_index(drop=True)
    final_df.to_excel("option_chain_all_indices.xlsx", index=False)
    print("\n✅ Success! Saved as option_chain_all_indices.xlsx")
else:
    print("❌ No data fetched.")
