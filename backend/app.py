from fastapi import FastAPI, Request, Body
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
import json
import os

from scraper import run_scraper
from database import check_usage, register_usage
from email_sender import send_excel

app = FastAPI()

templates = Jinja2Templates(directory="backend/templates")

SESSION_FILE = os.path.join(os.path.dirname(__file__), "session.json")


# =========================
# HOME
# =========================

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# =========================
# SAVE SESSION FROM EXTENSION
# =========================

@app.post("/save-session")
async def save_session(cookies: list = Body(...)):

    session = {
        "cookies": cookies,
        "origins": []
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(session, f)

    print("Session saved")

    return {"status": "session saved"}


# =========================
# RUN SCRAPER
# =========================

@app.get("/consulta/{ruc}")
async def consulta(request: Request, ruc: str):

    ip = request.client.host

    if not check_usage(ip):
        return {"error": "Límite de ejecuciones alcanzado (2)"}

    if not os.path.exists(SESSION_FILE):
        return {"error": "Debes conectar primero tu sesión SUNAT"}

    excel_path = await run_scraper(ruc)

    register_usage(ip)

    send_excel(excel_path)

    return FileResponse(
        excel_path,
        filename=f"sunat_{ruc}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )