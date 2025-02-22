import requests

url = "https://opensky-network.org/api/states/all"
response = requests.get(url)

if response.status_code == 200:
    print("All State Vectors Response:", response.json())
else:
    print("Error:", response.status_code, response.text)
