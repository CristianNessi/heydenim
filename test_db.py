from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://postgres:1802@localhost:5432/HeyDemin_db"
)

with engine.connect() as conn:
    print("OK DB")