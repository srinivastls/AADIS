from src.agents.base_agent import BaseAgent
from src.database.connection import db_manager
from src.models.document_models import TableData
import pandas as pd
from typing import Dict, List, Any
import json

class TableExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("TableExtractor")
    
    def process(self, layout_data: Dict[str, Any], document_id: int, file_path: str) -> List[Dict[str, Any]]:
        """Extract and process tables from layout data"""
        self.log_info("Starting table extraction and processing")
        
        extracted_tables = []
        
        db = db_manager.get_db_session()
        try:
            for idx, table_info in enumerate(layout_data.get("tables", [])):
                try:
                    # Extract table data using docling's table extraction
                    table_data = self._extract_table_data(table_info, file_path)
                    
                    if not table_data or len(table_data) == 0:
                        continue
                    
                    # Process table into structured format
                    structured_data = self._structure_table_data(table_data)
                    
                    # Create database record
                    table_record = TableData(
                        document_id=document_id,
                        table_data=structured_data,
                        caption=table_info.get("caption", ""),
                        page_number=table_info["page_number"],
                        bbox=table_info["bbox"],
                        headers=structured_data.get("headers", [])
                    )
                    
                    db.add(table_record)
                    
                    extracted_tables.append({
                        "table_id": idx,
                        "data": structured_data,
                        "page_number": table_info["page_number"],
                        "caption": table_info.get("caption", "")
                    })
                    
                except Exception as e:
                    self.log_error(f"Error processing table {idx}: {str(e)}")
                    continue
            
            db.commit()
        finally:
            db.close()
        
        self.log_info(f"Table extraction completed. Processed {len(extracted_tables)} tables")
        return extracted_tables
    
    def _extract_table_data(self, table_info: Dict[str, Any], file_path: str) -> List[List[str]]:
        """Extract raw table data"""
        # This would use docling's table extraction or fallback to other methods
        # For now, return the text content parsed as table
        text = table_info.get("text", "")
        if not text:
            return []
        
        # Simple table parsing - split by lines and cells
        lines = text.strip().split('\n')
        table_data = []
        
        for line in lines:
            # Split by common delimiters
            if '\t' in line:
                cells = line.split('\t')
            elif '|' in line:
                cells = line.split('|')
            else:
                cells = [line]
            
            cells = [cell.strip() for cell in cells if cell.strip()]
            if cells:
                table_data.append(cells)
        
        return table_data
    
    def _structure_table_data(self, raw_data: List[List[str]]) -> Dict[str, Any]:
        """Structure raw table data into organized format"""
        if not raw_data:
            return {}
        
        # Assume first row contains headers
        headers = raw_data[0] if raw_data else []
        rows = raw_data[1:] if len(raw_data) > 1 else []
        
        structured = {
            "headers": headers,
            "rows": rows,
            "num_columns": len(headers),
            "num_rows": len(rows)
        }
        
        # Convert to DataFrame-like structure for easier querying later
        if headers and rows:
            try:
                df_data = []
                for row in rows:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        value = row[i] if i < len(row) else ""
                        row_dict[header] = value
                    df_data.append(row_dict)
                
                structured["data"] = df_data
            except Exception as e:
                self.log_error(f"Error structuring table data: {str(e)}")
        
        return structured