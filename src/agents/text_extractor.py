from src.agents.base_agent import BaseAgent
from src.database.connection import db_manager
from src.models.document_models import TextBlock
from typing import Dict, List, Any

class TextExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("TextExtractor")
    
    def process(self, layout_data: Dict[str, Any], document_id: int) -> List[Dict[str, Any]]:
        """Extract and process text blocks from layout data"""
        self.log_info("Starting text extraction and processing")
        
        extracted_texts = []
        
        db = db_manager.get_db_session()
        try:
            for idx, text_block in enumerate(layout_data.get("text_blocks", [])):
                try:
                    # Clean and process text
                    cleaned_text = self._clean_text(text_block["text"])
                    
                    if len(cleaned_text.strip()) < 10:  # Skip very short texts
                        continue
                    
                    # Add to vector database
                    vector_id = db_manager.add_text_embedding(
                        text=cleaned_text,
                        metadata={
                            "document_id": document_id,
                            "block_type": text_block["type"],
                            "page_number": text_block["page_number"],
                            "reading_order": idx
                        }
                    )
                    
                    # Create database record
                    text_record = TextBlock(
                        document_id=document_id,
                        content=cleaned_text,
                        block_type=text_block["type"],
                        page_number=text_block["page_number"],
                        bbox=text_block["bbox"],
                        reading_order=idx,
                        vector_id=vector_id
                    )
                    
                    db.add(text_record)
                    
                    extracted_texts.append({
                        "content": cleaned_text,
                        "type": text_block["type"],
                        "page_number": text_block["page_number"],
                        "vector_id": vector_id
                    })
                    
                except Exception as e:
                    self.log_error(f"Error processing text block {idx}: {str(e)}")
                    continue
            
            db.commit()
        finally:
            db.close()
        
        self.log_info(f"Text extraction completed. Processed {len(extracted_texts)} text blocks")
        return extracted_texts
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"]+', '', text)
        
        return text.strip()