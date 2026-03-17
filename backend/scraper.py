import asyncio
import os
import re
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError
import socket
import getpass

# =========================
# CONFIG
# =========================

URL_BUZON = "https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm?exe=buzon"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "../output")
EXCEL_PATH = os.path.join(OUTPUT_DIR, "correos.xlsx")

os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_MENSAJES_DEMO = 50

# =========================
# UTILS
# =========================

def _normalize_numero_resolucion(titulo: str) -> str:
    if not titulo:
        return ""
    m = re.search(r"\b\d{3}-\d{3}-\d{7}\b", titulo)
    return m.group(0) if m else ""


def _normalize_tipo_resolucion(titulo: str) -> str:
    if not titulo:
        return ""
    t = titulo.lower()
    if "devoluc" in t:
        return "Devolución"
    if "multa" in t:
        return "Multa"
    if "determin" in t:
        return "Determinación"
    if "cobranza" in t:
        return "Cobranza"
    if "fracc" in t:
        return "Fraccionamiento"
    if "fiscaliz" in t:
        return "Fiscalización"
    return "Otro"


async def detect_ruc_from_session(page) -> str:

    pat = re.compile(r"\bRUC\s*(?:N\s*[°º]?\s*)?[:\s]*([0-9]{11})\b", re.IGNORECASE)

    for fr in page.frames:
        try:
            txt = await fr.inner_text("body")
            m = pat.search(txt or "")
            if m:
                return m.group(1)
        except:
            pass

    return ""


async def extract_cuerpo_from_detail(page):

    try:
        return (await page.inner_text("div.contenedor-correo")).strip()
    except:
        return ""


# =========================
# SCRAPER PRINCIPAL
# =========================

async def run_scraper(ruc_input):

    nuevos = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        SESSION_FILE = os.path.join(BASE_DIR, "session.json")

        context = await browser.new_context(
            storage_state=SESSION_FILE
        )
        page = await context.new_page()

        print("Abriendo SUNAT...")

        await page.goto(URL_BUZON)

        print("Verificando sesión SUNAT...")

        try:
            await page.wait_for_selector("#listaMensajes", timeout=10000)
        except TimeoutError:

            await browser.close()

            raise Exception(
                "Debes loguearte primero en SUNAT usando el botón 'Abrir SUNAT'."
            )
        ruc = await detect_ruc_from_session(page) or ruc_input

        ip_cliente = socket.gethostbyname(socket.gethostname())
        user_id = getpass.getuser()

        mensajes = await page.query_selector_all("#listaMensajes > li")

        for i, msg in enumerate(mensajes):

            if i >= MAX_MENSAJES_DEMO:
                break

            msg_id = await msg.get_attribute("id")

            titulo_el = await msg.query_selector("a.linkMensaje")

            if not titulo_el:
                continue

            titulo = (await titulo_el.inner_text()).strip()

            clasif_sunat = ""

            try:
                lab = await msg.query_selector("span.label")
                if lab:
                    clasif_sunat = (await lab.inner_text()).strip()
            except:
                pass

            await titulo_el.click()

            try:
                await page.wait_for_selector(
                    "div.contenedor-correo, div.panel-body",
                    timeout=20000
                )
            except TimeoutError:
                continue

            cuerpo = await extract_cuerpo_from_detail(page)

            fecha_notificacion = ""

            try:
                raw = (
                    await page.locator("#idFechaDetalle")
                    .first.inner_text()
                ).strip()

                dt = datetime.strptime(
                    raw,
                    "%d/%m/%Y %H:%M:%S"
                )

                fecha_notificacion = dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            except:
                pass

            fecha_scrap = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            numero_res = _normalize_numero_resolucion(titulo)
            tipo_res = _normalize_tipo_resolucion(titulo)

            nuevos.append({

                "RUC": ruc,
                "IP": ip_cliente,
                "USER_ID": user_id,

                "id": msg_id,
                "titulo": titulo,
                "Clasificacion_SUNAT": clasif_sunat,

                "Fecha_Notificacion": fecha_notificacion,
                "fecha_scrap": fecha_scrap,

                "contenido": cuerpo,
                "pdfs": "",

                "Numero_Tipo": numero_res,
                "Tipo_Resolucion": tipo_res,

                "Nombre_Adjunto": "",
                "Tamaño_Adjunto": "",
                "Presencia_Adjunto": "No",
                "Ruta_Local": ""
            })

        await browser.close()

    df = pd.DataFrame(nuevos)

    df.to_excel(EXCEL_PATH, index=False)

    return EXCEL_PATH