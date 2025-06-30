import requests
import pandas as pd
import os
from datetime import datetime

def fetch_and_save_option_chain(index_name, instrument_key, expiry_date, token):
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry_date}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch data for {index_name}: {response.status_code}")
        return None

    data = response.json()
    if "data" not in data:
        print(f"❌ Invalid response for {index_name}")
        return None

    chain_data = data["data"]
    print(f"\n🔍 Sample data for {index_name}:")
    if chain_data:
        print(chain_data[0])
    else:
        print("⚠️ No data returned for this index.")
        return None

    records = []
    for entry in chain_data:
        strike = entry.get("strike_price", 0)
        ce = entry.get("call_options") or {}
        pe = entry.get("put_options") or {}

        ce_market = ce.get("market_data") or {}
        pe_market = pe.get("market_data") or {}

        ce_iv = (ce.get("option_greeks") or {}).get("iv", 0)
        pe_iv = (pe.get("option_greeks") or {}).get("iv", 0)

        record = {
            "Strike Price": strike,
            "CE LTP": ce_market.get("ltp"),
            "CE OI": ce_market.get("oi"),
            "CE Volume": ce_market.get("volume"),
            "CE Change OI": ce_market.get("oi", 0) - ce_market.get("prev_oi", 0),
            "CE IV": ce_iv,

            "PE LTP": pe_market.get("ltp"),
            "PE OI": pe_market.get("oi"),
            "PE Volume": pe_market.get("volume"),
            "PE Change OI": pe_market.get("oi", 0) - pe_market.get("prev_oi", 0),
            "PE IV": pe_iv
        }
        records.append(record)

    df = pd.DataFrame(records)
    df.sort_values("Strike Price", inplace=True)
    return df

if __name__ == "__main__":
    ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyTkNTVTUiLCJqdGkiOiI2ODYyMWNiMGM5NTJjNDM5Y2YzZDk5MWQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzUxMjYwMzM2LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTEzMjA4MDB9.eSR40n9lS6MJ06ngyy3hbYC6vpRdLz1zYWGhJNnsOuQ"
    EXPIRY_DATE = "2025-07-03"

    indices = {
        "NIFTY": "NSE_INDEX|Nifty 50"
    }

    writer = pd.ExcelWriter("option_chain_all_indices.xlsx", engine="openpyxl")

    data_written = False
    for index_name, instrument_key in indices.items():
        df = fetch_and_save_option_chain(index_name, instrument_key, EXPIRY_DATE, ACCESS_TOKEN)
        if df is not None and not df.empty:
            df.to_excel(writer, sheet_name=index_name, index=False)
            data_written = True

    if not data_written:
        pd.DataFrame({"Error": ["No valid data fetched."]}).to_excel(writer, sheet_name="ERROR", index=False)

    writer.close()
    print("✅ Option chain saved to option_chain_all_indices.xlsx")
