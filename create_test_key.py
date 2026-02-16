# create_test_key.py

from billing.database import SessionLocal, engine, Base
from billing.models import User, ApiKey, generate_api_key


def main():
    # (Re)crée les tables si besoin
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # créer un user
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    # créer une clé API avec un quota de 5
    key_value = generate_api_key()
    api_key = ApiKey(
        key=key_value,
        user_id=user.id,
        quota_remaining=5,
    )
    db.add(api_key)
    db.commit()

    print("Nouvelle API key :", key_value)
    print("Quota :", api_key.quota_remaining)

    db.close()


if __name__ == "__main__":
    main()
