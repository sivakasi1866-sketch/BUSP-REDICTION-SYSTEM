from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

_is_sqlite = "sqlite" in settings.DATABASE_URL
_is_postgres = "postgresql" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL

# Build engine kwargs
_engine_kwargs = {}

if _is_sqlite:
    # SQLite needs check_same_thread=False for FastAPI thread model
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
elif _is_postgres:
    # Neon (serverless PostgreSQL) requires pool_pre_ping to handle dropped connections
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
