from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from scraper import run_scraper
from database import check_usage, register_usage
from email_sender import send_excel

app = FastAPI()

templates = Jinja2Templates(directory="backend/templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/consulta/{ruc}")
async def consulta(request: Request, ruc: str):

    ip = request.client.host

    if not check_usage(ip):
        return {"error": "Límite de ejecuciones alcanzado (2)"}

    excel_path = await run_scraper(ruc)

    register_usage(ip)

    send_excel(excel_path)

    return FileResponse(
        excel_path,
        filename=f"sunat_{ruc}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )