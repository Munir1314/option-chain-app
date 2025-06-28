import requests

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyTkNTVTUiLCJqdGkiOiI2ODVmZmMyMDk2ZDE4ODdiMjFmYzI0NDgiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzUxMTIwOTI4LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTExNDgwMDB9.E07aDE8ci9ZSMVGFBecJ0j5aObVABS34nFdRrxPLa-g"

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

url = "https://api.upstox.com/v2/option/chain?instrument_key=NSE_INDEX_NIFTY"

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
