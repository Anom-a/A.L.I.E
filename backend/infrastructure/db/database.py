from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from infrastructure.config import load_config

# Initialize engine lazily
engine = None
SessionLocal = None
Base = declarative_base()

def init_db(database_url: str):
    global engine, SessionLocal
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
