from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
import json
import os

from backend.scraper import run_scraper
from backend.database import check_usage, register_usage
from backend.email_sender import send_excel

app = FastAPI()

# =========================
# PATHS
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

SESSION_FILE = "/tmp/session.json"


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
async def save_session(request: Request):

    try:
        data = await request.json()
        print("DATA RECIBIDA:", data)
    except:
        return {"error": "No se pudo leer el JSON"}

    if "cookies" not in data:
        return {"error": "Formato inválido: falta 'cookies'"}

    session = {
        "cookies": data["cookies"],
        "origins": []
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(session, f)

    print("✅ Session guardada correctamente")

    return {"status": "session saved"}


# =========================
# RUN SCRAPER
# =========================

@app.get("/consulta/{ruc}")
async def consulta(request: Request, ruc: str):

    ip = request.client.host

    # Control de uso
    if not check_usage(ip):
        return {"error": "Límite de ejecuciones alcanzado (2)"}

    # Validar sesión
    if not os.path.exists(SESSION_FILE):
        return {"error": "Debes conectar primero tu sesión SUNAT"}

    try:
        excel_path = await run_scraper(ruc)
    except Exception as e:
        print(f"❌ Error en scraper: {e}")
        return {"error": "Error ejecutando scraper"}

    register_usage(ip)

    try:
        send_excel(excel_path)
    except Exception as e:
        print(f"⚠️ Error enviando correo: {e}")

    return FileResponse(
        excel_path,
        filename=f"sunat_{ruc}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )