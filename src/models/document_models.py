
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy import Float

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    filepath = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    metadata = Column(JSON)
    
    # Relationships
    text_blocks = relationship("TextBlock", back_populates="document")
    tables = relationship("TableData", back_populates="document")
    images = relationship("ImageData", back_populates="document")
    file_hash = Column(String, unique=True, index=True)  # Prevent duplicate processing
    processing_time = Column(Float)
    total_pages = Column(Integer, default=0)
    word_count = Column(Integer, default=0)

class TextBlock(Base):
    __tablename__ = "text_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text)
    block_type = Column(String)  # paragraph, heading, list, etc.
    page_number = Column(Integer)
    bbox = Column(JSON)  # bounding box coordinates
    reading_order = Column(Integer)
    vector_id = Column(String)  # Reference to vector in Chroma
    content_hash = Column(String, index=True)  # For deduplication
    confidence_score = Column(Float, default=1.0)
    word_count = Column(Integer, default=0)
    
    document = relationship("Document", back_populates="text_blocks")

class TableData(Base):
    __tablename__ = "tables"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    table_data = Column(JSON)  # Structured table data
    caption = Column(Text)
    page_number = Column(Integer)
    bbox = Column(JSON)
    headers = Column(JSON)
    
    document = relationship("Document", back_populates="tables")

class ImageData(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    image_path = Column(String)
    caption = Column(Text)
    alt_text = Column(Text)
    page_number = Column(Integer)
    bbox = Column(JSON)
    image_type = Column(String)
    
    document = relationship("Document", back_populates="images")

# Pydantic models for API/data transfer
class DocumentCreate(BaseModel):
    filename: str
    filepath: str
    file_type: str
    file_size: int

class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

from sqlalchemy import Index
Index('ix_document_status', Document.status)
Index('ix_text_page_order', TextBlock.document_id, TextBlock.page_number, TextBlock.reading_order)