import requests

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyTkNTVTUiLCJqdGkiOiI2ODYyMWNiMGM5NTJjNDM5Y2YzZDk5MWQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzUxMjYwMzM2LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTEzMjA4MDB9.eSR40n9lS6MJ06ngyy3hbYC6vpRdLz1zYWGhJNnsOuQ"
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
