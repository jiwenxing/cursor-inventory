from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# 获取backend目录的绝对路径
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# 确保data目录存在
DATA_DIR.mkdir(exist_ok=True)

# SQLite数据库路径（使用绝对路径）
DATABASE_URL = f"sqlite:///{DATA_DIR / 'app.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
Base.__table_args__ = {'sqlite_autoincrement': True}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
