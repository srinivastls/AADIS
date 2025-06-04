
import docling
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from src.agents.base_agent import BaseAgent
import fitz  # PyMuPDF
from typing import Dict, List, Any

class LayoutAnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__("LayoutAnalyzer")
        
        # Configure docling pipeline
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: pipeline_options,
            }
        )
    
    def process(self, file_path: str) -> Dict[str, Any]:
        """Analyze document layout and extract structure"""
        self.log_info(f"Analyzing layout for: {file_path}")
        
        try:
            # Use docling for primary analysis
            result = self.converter.convert(file_path)
            doc = result.document
            
            layout_info = {
                "pages": [],
                "total_pages": len(doc.pages),
                "text_blocks": [],
                "tables": [],
                "images": []
            }
            
            for page_num, page in enumerate(doc.pages):
                page_info = {
                    "page_number": page_num + 1,
                    "page_size": {
                        "width": page.size.width if page.size else 0,
                        "height": page.size.height if page.size else 0
                    },
                    "blocks": []
                }
                
                # Extract text blocks with layout information
                for element in page.elements:
                    if hasattr(element, 'text') and element.text:
                        block_info = {
                            "type": element.__class__.__name__.lower(),
                            "text": element.text,
                            "bbox": {
                                "x0": element.bbox.l if element.bbox else 0,
                                "y0": element.bbox.t if element.bbox else 0,
                                "x1": element.bbox.r if element.bbox else 0,
                                "y1": element.bbox.b if element.bbox else 0
                            }
                        }
                        
                        if "table" in block_info["type"]:
                            layout_info["tables"].append({
                                **block_info,
                                "page_number": page_num + 1
                            })
                        else:
                            layout_info["text_blocks"].append({
                                **block_info,
                                "page_number": page_num + 1
                            })
                        
                        page_info["blocks"].append(block_info)
                
                layout_info["pages"].append(page_info)
            
            # Also extract images using PyMuPDF for better image handling
            pdf_doc = fitz.open(file_path)
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    layout_info["images"].append({
                        "page_number": page_num + 1,
                        "image_index": img_index,
                        "xref": img[0],
                        "bbox": page.get_image_bbox(img)
                    })
            
            pdf_doc.close()
            
            self.log_info(f"Layout analysis completed. Found {len(layout_info['text_blocks'])} text blocks, "
                         f"{len(layout_info['tables'])} tables, {len(layout_info['images'])} images")
            
            return layout_info
            
        except Exception as e:
            self.log_error(f"Layout analysis failed: {str(e)}")
            raise
