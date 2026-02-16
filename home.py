
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pypandoc
import uuid
import os 
import subprocess
import tempfile
from pathlib import Path
import shutil


app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    # Nom unique
    file_id = str(uuid.uuid4())
    input_path = f"{UPLOAD_DIR}/{file_id}_{file.filename}"
    output_path = f"{UPLOAD_DIR}/{file_id}.pdf"

    # Sauvegarde du fichier
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Conversion
    pypandoc.convert_file(
        input_path,
        "pdf",
        outputfile=output_path,
        extra_args=["--standalone"]
    )

    return FileResponse(output_path, media_type="application/pdf", filename="converted.pdf")

