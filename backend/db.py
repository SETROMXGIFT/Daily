"""
Conexión a la base de datos.

En producción, DATABASE_URL apunta a un Postgres en la nube (Supabase, Neon,
Railway, etc.) — así el PC y el celular leen y escriben en la MISMA base de
datos y todo queda sincronizado automáticamente.

Si no se define DATABASE_URL, cae a un sqlite local (útil solo para probar
el backend en tu máquina durante el desarrollo).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./diario_local.db")

# Render/Railway a veces entregan "postgres://", SQLAlchemy 2.x quiere "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
