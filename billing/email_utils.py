# billing/email_utils.py

import os
import smtplib
from email.message import EmailMessage


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)  # expéditeur par défaut


def send_api_key_email(to_email: str, api_key: str, quota: int, base_url: str):
    """
    Envoie un email à l'utilisateur avec sa clé API et son quota.
    Si la config SMTP est absente, on log et on ne fait rien.
    """

    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM]):
        # En prod, tu peux logger ça proprement
        print("[WARN] SMTP non configuré, email non envoyé.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Votre clé API - Service PDF"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    msg.set_content(
        f"""Bonjour,

Merci pour votre achat !

Voici votre clé API pour le service de conversion PDF :

    Clé API : {api_key}
    Quota : {quota} conversions

Exemple d'appel via curl :

curl -X POST \\
  -H "X-API-Key: {api_key}" \\
  -F "file=@votre_fichier.docx" \\
  https://ton-domaine.com/convert \\
  --output resultat.pdf

Gardez cette clé secrète et ne la partagez pas.

Cordialement,
Le service PDF
"""
    )

    # conversion en int pour le port
    port = int(SMTP_PORT)

    with smtplib.SMTP(SMTP_HOST, port) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)

    print(f"[INFO] Email envoyé à {to_email}")
