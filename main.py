# main.py

import subprocess
import tempfile
from pathlib import Path
import shutil
from billing.routes_checkout import router as checkout_router
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from billing.mock_stripe import router as mock_stripe_router
from billing.routes_checkout import router as checkout_router
from billing.mock_stripe import router as mock_stripe_router
from billing.service_api_key import verify_api_key
from billing.database import get_db, Base, engine
from fastapi.staticfiles import StaticFiles
from billing.routes_webhook import router as webhook_router
from fastapi.responses import RedirectResponse
from billing.routes_account import router as account_router
from billing.routes_paypal import router as paypal_router
from fastapi import FastAPI, UploadFile, File, HTTPException
import pdfplumber
import arabic_reshaper
from bidi.algorithm import get_display
import io



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
app.include_router(paypal_router)





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


app.mount("/static", StaticFiles(directory="static"), name="static")

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


@app.post("/convert", response_class=FileResponse)
async def convert_endpoint(
    file: UploadFile = File(...),
    api_key = Depends(verify_api_key),  # ApiKey en DB
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    try:
        pdf_path = convert_to_pdf(file)

        # 🔽 décrémentation du quota
        if api_key.quota_remaining is not None:
            api_key.quota_remaining -= 1
            db.add(api_key)
            db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FileResponse(
        path=pdf_path,
        filename=pdf_path.name,
        media_type="application/pdf",
    )




@app.get("")
async def health():
    return FileResponse("home.html")


@app.post("/convert-rtl")
async def convert_rtl_pdf(file: UploadFile = File(...)):
    # Vérification de l'extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")

    try:
        # Lecture du contenu en mémoire sans enregistrer sur le disque
        pdf_content = await file.read()
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            final_pages = []
            
            for page in pdf.pages:
                # 1. Extraction du texte brut
                raw_text = page.extract_text()
                
                if raw_text:
                    # 2. Reshaping : Connecte les lettres arabes entre elles
                    # (Essentiel pour que 'f-l-m' devienne 'film')
                    reshaped_text = arabic_reshaper.reshape(raw_text)
                    
                    # 3. Bidi : Inverse l'ordre visuel pour le RTL
                    bidi_text = get_display(reshaped_text)
                    
                    final_pages.append(bidi_text)
                else:
                    final_pages.append("[Page vide ou image sans texte]")

            return {
                "filename": file.filename,
                "language_support": "RTL (Arabic/Hebrew)",
                "content": "\n\n--- Page Break ---\n\n".join(final_pages)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la conversion : {str(e)}")

