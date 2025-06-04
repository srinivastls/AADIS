from src.agents.base_agent import BaseAgent
from src.agents.layout_analyzer import LayoutAnalyzerAgent
from src.agents.text_extractor import TextExtractionAgent
from src.agents.table_extractor import TableExtractionAgent
from src.agents.image_processor import ImageProcessingAgent
from src.database.connection import db_manager
from src.models.document_models import Document, DocumentCreate
from datetime import datetime
from typing import Dict, Any
import os

class DocumentProcessingCoordinator(BaseAgent):
    def __init__(self):
        super().__init__("Coordinator")
        
        # Initialize specialized agents
        self.layout_analyzer = LayoutAnalyzerAgent()
        self.text_extractor = TextExtractionAgent()
        self.table_extractor = TableExtractionAgent()
        self.image_processor = ImageProcessingAgent()
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Coordinate the full document processing pipeline"""
        self.log_info(f"Starting document processing pipeline for: {file_path}")
        
        # Create document registry entry
        document_id = self._register_document(file_path)
        
        try:
            # Update status to processing
            self._update_document_status(document_id, "processing")
            
            # Phase 1: Layout Analysis
            self.log_info("Phase 1: Layout Analysis")
            layout_data = self.layout_analyzer.process(file_path)
            
            # Phase 2: Content Extraction using specialized agents
            self.log_info("Phase 2: Content Extraction")
            
            # Text extraction
            text_results = self.text_extractor.process(layout_data, document_id)
            
            # Table extraction  
            table_results = self.table_extractor.process(layout_data, document_id, file_path)
            
            # Image processing
            image_results = self.image_processor.process(layout_data, document_id, file_path)
            
            # Update status to completed
            self._update_document_status(document_id, "completed")
            
            results = {
                "document_id": document_id,
                "status": "completed",
                "summary": {
                    "text_blocks": len(text_results),
                    "tables": len(table_results),
                    "images": len(image_results),
                    "total_pages": layout_data.get("total_pages", 0)
                },
                "details": {
                    "layout": layout_data,
                    "text": text_results,
                    "tables": table_results,
                    "images": image_results
                }
            }
            
            self.log_info(f"Document processing completed successfully. "
                         f"Extracted: {len(text_results)} text blocks, "
                         f"{len(table_results)} tables, {len(image_results)} images")
            
            return results
            
        except Exception as e:
            self.log_error(f"Document processing failed: {str(e)}")
            self._update_document_status(document_id, "failed")
            raise

    
    
    def _register_document(self, file_path: str) -> int:
        """Register document in database"""
        db = db_manager.get_db_session()
        try:
            file_stat = os.stat(file_path)
            
            doc_create = DocumentCreate(
                filename=os.path.basename(file_path),
                filepath=file_path,
                file_type=os.path.splitext(file_path)[1].lower(),
                file_size=file_stat.st_size
            )
            
            document = Document(**doc_create.model_dump())
            db.add(document)
            db.commit()
            db.refresh(document)
            
            return document.id
        finally:
            db.close()
    

    def _update_document_status(self, document_id: int, status: str):
        """Update document processing status"""
        db = db_manager.get_db_session()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = status
                if status == "completed":
                    document.processed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()


