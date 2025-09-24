from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    services = relationship("Service", back_populates="application", cascade="all, delete-orphan")
    schemas = relationship("Schema", back_populates="application", cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="services")
    schemas = relationship("Schema", back_populates="service", cascade="all, delete-orphan")

class Schema(Base):
    __tablename__ = "schemas"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_format = Column(String(10), nullable=False)  # json or yaml
    file_size = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256 hash
    is_latest = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="schemas")
    service = relationship("Service", back_populates="schemas")

# Database setup
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
