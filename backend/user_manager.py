import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.pool import NullPool
from cryptography.fernet import Fernet

load_dotenv()
logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sessions = relationship("DBSession", back_populates="user")
    histories = relationship("QueryHistory", back_populates="user")

class DBSession(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    db_type = Column(String(50), nullable=False)
    encrypted_details = Column(Text, nullable=False) # Stores JSON of host, port, db, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")
    histories = relationship("QueryHistory", back_populates="session")

class QueryHistory(Base):
    __tablename__ = 'query_history'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    database_name = Column(String(100), nullable=True) # Tracks which database this query hit
    nl_query = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    model_used = Column(String(100))
    execution_time = Column(String(50))
    row_count = Column(Integer)
    success = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="histories")
    session = relationship("DBSession", back_populates="histories")

class UserManager:
    def __init__(self):
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL is not set in .env")
        
        # SQLAlchemy requires postgresql:// instead of postgres://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        connect_args = {}
        if db_url.startswith("postgresql"):
            connect_args = {
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
            
        self.engine = create_engine(
            db_url,
            connect_args=connect_args,
            poolclass=NullPool,
            pool_reset_on_return=None
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Ensure tables exist
        Base.metadata.create_all(bind=self.engine)
        logger.info("Neon database tables ensured")
        
        # Setup Encryption Context
        self._init_encryption()

    def _init_encryption(self):
        env_key = os.getenv("FERNET_KEY")
        if not env_key:
            raise ValueError("FERNET_KEY environment variable is missing. It is strictly required for encrypting session details.")
        self.cipher = Fernet(env_key.encode())

    def encrypt_dict(self, data: dict) -> str:
        return self.cipher.encrypt(json.dumps(data).encode()).decode()

    def decrypt_dict(self, encrypted_data: str) -> dict:
        return json.loads(self.cipher.decrypt(encrypted_data.encode()).decode())

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

user_manager = UserManager()
