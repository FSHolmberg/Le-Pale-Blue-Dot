from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    anonymous_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    invite_code = Column(String, nullable=True)
    
    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default="active")  # active, warning_15min, kicked, ended
    crisis_flag_date = Column(String, nullable=True)  # ISO date string
    weather = Column(String, nullable=True)
    message_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    agent = Column(String, nullable=False)  # "user", "bart", "bernie", etc.
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_user_message = Column(Integer, default=0)  # 0=agent, 1=user (SQLite compat)
    
    session = relationship("Session", back_populates="messages")

# Database connection
DATABASE_URL = "postgresql://localhost/lpbd_dev"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Create all tables"""
    Base.metadata.create_all(engine)

def get_db():
    """Dependency for FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()