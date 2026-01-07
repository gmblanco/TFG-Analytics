import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("X_BEARER_TOKEN")

url = "https://api.x.com/2/tweets/search/recent"
params = {
    "query": '(artificial intelligence OR AI) lang:en -is:retweet',
    "max_results": 10,
    "tweet.fields": "created_at,public_metrics,lang",
}

headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers, params=params, timeout=30)

print("Status:", response.status_code)
print(response.text[:500])
