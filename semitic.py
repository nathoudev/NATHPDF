from fastapi import FastAPI, UploadFile, File, HTTPException
import pdfplumber
import arabic_reshaper
from bidi.algorithm import get_display
import io
from fastapi import APIRouter, UploadFile, File
# ... tes autres imports (pdfplumber, etc.)

router = APIRouter()


@router.post("/convert-rtl")
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
