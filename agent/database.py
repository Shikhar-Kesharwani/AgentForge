import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# -------------------------------------------------------------------
# DUAL-MODEL DATABASE CONFIGURATION
# -------------------------------------------------------------------
# Model 1: Local Docker Stack (SQLite)
# Model 2: Managed Cloud Stack (PostgreSQL via DATABASE_URL)
# -------------------------------------------------------------------

# Check for cloud database URL (e.g., Render/Neon Postgres)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # If the URL is provided by a cloud provider like Render, it might start with postgres://
    # SQLAlchemy 1.4+ requires postgresql:// instead.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    print("☁️  Using Managed Cloud Database (PostgreSQL)")
    engine = create_engine(DATABASE_URL)
else:
    print("🏠 Using Local Standalone Database (SQLite)")
    # Default to local SQLite DB inside the container/workspace
    DB_DIR = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
    os.makedirs(DB_DIR, exist_ok=True)
    sqlite_url = f"sqlite:///{os.path.join(DB_DIR, 'agentforge.db')}"
    
    # SQLite needs check_same_thread=False for FastAPI
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------------------------------------------------
# DATA MODELS
# -------------------------------------------------------------------
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    role = Column(String(50))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Initialize the tables (in a production system, use Alembic for migrations)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
