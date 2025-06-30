import requests

# 🔑 Step 1: Fill in your credentials below
API_KEY = "b2096ceb-fc87-4774-8b45-25f9a55339e6"
API_SECRET = "n8spbqym2a"
REDIRECT_URI = "https://127.0.0.1"
AUTH_CODE = "vge0St"  # This must be the full code from ?code=... (check again)

# 📡 Step 2: Upstox token URL
url = "https://api.upstox.com/v2/login/authorization/token"

# 📦 Step 3: Build the payload for the POST request
payload = {
    "client_id": API_KEY,
    "client_secret": API_SECRET,
    "code": AUTH_CODE,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code"
}

# 🧾 Step 4: Set headers (telling server we're sending form data)
headers = {
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded"
}

# 🚀 Step 5: Make the POST request to exchange code for token
response = requests.post(url, data=payload, headers=headers)

# 📊 Step 6: Print the result
print(response.json())
