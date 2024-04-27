import requests

res = requests.post("http://127.0.0.1:8000/api/pipelines/telegram_test/run")
print(res.json())