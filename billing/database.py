# billing/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# On lit l'URL de la base depuis l'environnement (voir docker-compose.yml)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pdfuser:pdfpassword@db:5432/pdfbilling",
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
