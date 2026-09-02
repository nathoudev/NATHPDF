
# main.py

import subprocess
import tempfile
from pathlib import Path
import shutil

import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request 
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from billing.mock_stripe import router as mock_stripe_router
from billing.routes_checkout import router as checkout_router
from billing.service_api_key import verify_api_key
from billing.database import get_db, Base, engine
from fastapi.staticfiles import StaticFiles
from billing.routes_webhook import router as webhook_router
from fastapi.responses import RedirectResponse
from billing.routes_account import router as account_router

from datetime import date
from billing.models import DailyConversion

from semitic import router as semitic_router

ENV = os.getenv("ENV", "dev")



app = FastAPI(
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
)


app.include_router(checkout_router)
app.include_router(mock_stripe_router)
app.include_router(webhook_router)
app.include_router(account_router)


app.include_router(semitic_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

if os.environ.get("MOCK_STRIPE", "0") == "1":
    app.mount("/dev-static", StaticFiles(directory="dev-static"), name="dev-static")
@app.get("/static/mock-buy.html")
async def block_mock_buy_page():
    if not MOCK_STRIPE:
        # En prod -> 404
        raise HTTPException(status_code=404, detail="Not found")
    # En dev, on laisse StaticFiles servir la page
    raise HTTPException(status_code=307, detail="Redirect")  

    # pas idéal



if ENV != "prod":
    from billing.mock_stripe import router as mock_stripe_router
    app.include_router(mock_stripe_router)



@app.get("/buy")
async def buy_redirect():
    return RedirectResponse(url="/static/buy.html")

# 🔧 Création des tables au démarrage (dev / test)
Base.metadata.create_all(bind=engine)


def convert_to_pdf(upload_file: UploadFile) -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    input_path = temp_dir / upload_file.filename

    with open(input_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(temp_dir),
        str(input_path),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Erreur LibreOffice: {result.stderr.decode(errors='ignore')}")

    output_path = input_path.with_suffix(".pdf")
    if not output_path.exists():
        raise RuntimeError("Conversion échouée.")

    return output_path




def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"
@app.post("/convert", response_class=FileResponse)
async def convert_endpoint(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Aucun fichier fourni"
        )

    client_ip = get_client_ip(request)

    # --------------------------------
    # 1. Récupération de l'IP
    # --------------------------------


    today = date.today().isoformat()

    # --------------------------------
    # 2. Chercher le compteur du jour
    # --------------------------------

    usage = (
        db.query(DailyConversion)
        .filter(
            DailyConversion.ip_address == client_ip,
            DailyConversion.conversion_date == today,
        )
        .first()
    )

    # --------------------------------
    # 3. Vérifier la limite
    # --------------------------------

    if usage and usage.count >= 3:
        raise HTTPException(
            status_code=429,
            detail="Limite de 3 conversions gratuites atteinte pour aujourd'hui."
        )

    # --------------------------------
    # 4. Conversion
    # --------------------------------

    try:
        pdf_path = convert_to_pdf(file)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    # --------------------------------
    # 5. Conversion réussie -> +1
    # --------------------------------

    if usage:
        usage.count += 1
    else:
        usage = DailyConversion(
            ip_address=client_ip,
            conversion_date=today,
            count=1,
        )
        db.add(usage)

    db.commit()
    remaining = max(0, 3 - usage.count)

    # --------------------------------
    # 6. Retour du PDF
    # --------------------------------

    return FileResponse(
    path=pdf_path,
    filename=pdf_path.name,
    media_type="application/pdf",
    headers={
        "X-Free-Conversions-Remaining": str(remaining)
    },
)
    



@app.get("/")
async def health():
    return FileResponse("static/index4.html")


@app.get("/usage")
async def get_usage(
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = get_client_ip(request)
    today = date.today().isoformat()

    usage = (
        db.query(DailyConversion)
        .filter(
            DailyConversion.ip_address == client_ip,
            DailyConversion.conversion_date == today,
        )
        .first()
    )

    used = usage.count if usage else 0
    remaining = max(0, 3 - used)

    return {
        "limit": 3,
        "used": used,
        "remaining": remaining,
    }
# Monte le dossier static (pour le CSS/JS si besoin)


# Crée une route pour servir ton HTML
@app.get("/semitic")
async def get_semitic_page():
    return FileResponse("static/semiticpdf.html")




