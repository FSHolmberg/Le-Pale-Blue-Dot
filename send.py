

import requests
import time

while True:
    user_text = input("You: ").strip()
    if user_text.lower() in {"quit", "exit"}:
        break

    body = {
        "user_id": "dev",
        "text": user_text,
        "timestamp": time.time()
    }

    r = requests.post("http://127.0.0.1:8000/chat", json=body)
    print("LPBD:", r.json())
