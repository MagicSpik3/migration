import requests
import json

# Exact settings from your working curl command
url = "http://localhost:11434/api/generate"
model = "qwen2.5-coder:latest"
prompt = "Are you working?"

print(f"--- TESTING CONNECTION ---")
print(f"Target URL: {url}")
print(f"Target Model: '{model}'") # Quotes help spot trailing spaces

payload = {
    "model": model,
    "prompt": prompt,
    "stream": False
}

try:
    print("Sending request...")
    response = requests.post(url, json=payload, timeout=120)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS!")
        print("Response:", response.json()['response'])
    else:
        print("❌ FAILURE")
        print("Error Text:", response.text)

except Exception as e:
    print(f"❌ EXCEPTION: {e}")