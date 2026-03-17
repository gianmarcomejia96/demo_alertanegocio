import json
from fastapi import Body

SESSION_PATH = "backend/session.json"

@app.post("/save-session")
async def save_session(data: dict = Body(...)):

    cookies = data.get("cookies", [])

    with open("session.json", "w") as f:
        json.dump({"cookies": cookies}, f)

    return {"status": "session stored"}