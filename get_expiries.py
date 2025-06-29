import requests

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyTkNTVTUiLCJqdGkiOiI2ODYwZDViY2UxNTM3MTIwMThhYjM5NzQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzUxMTc2NjM2LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTEyMzQ0MDB9.6D4-lAVlxbOE25kyoClSSeDhvuRR1OmgneR0i1ei2XA"

# ✅ Correct instrument key format with space
instrument_key = "NSE_INDEX|Nifty 50"

url = f"https://api.upstox.com/v2/option/contract?instrument_key={instrument_key}"
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)

try:
    json_data = response.json()
    data = json_data.get("data")

    # This format should now work
    if isinstance(data, dict) and "expiry_dates" in data:
        expiries = data["expiry_dates"]
    elif isinstance(data, list) and data and "expiry_dates" in data[0]:
        expiries = data[0]["expiry_dates"]
    else:
        print("❌ Could not find expiry_dates")
        print("Data:", data)
        exit()

    print("\n✅ Available Expiries:")
    for exp in expiries:
        print("-", exp)

except Exception as e:
    print("❌ JSON parse error:", e)
    print("Raw response:", response.text)
