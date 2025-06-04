
from src.agents.base_agent import BaseAgent
from src.database.connection import db_manager
from src.models.document_models import ImageData
from config.settings import settings
import fitz  # PyMuPDF
from PIL import Image
import io
from pathlib import Path
from typing import Dict, List, Any

class ImageProcessingAgent(BaseAgent):
    def __init__(self):
        super().__init__("ImageProcessor")
        self.images_dir = settings.IMAGES_DIR
        self.images_dir.mkdir(exist_ok=True)
    
    def process(self, layout_data: Dict[str, Any], document_id: int, file_path: str) -> List[Dict[str, Any]]:
        """Extract and process images from document"""
        self.log_info("Starting image extraction and processing")
        
        extracted_images = []
        
        db = db_manager.get_db_session()
        try:
            # Open the PDF document
            pdf_doc = fitz.open(file_path)
            
            for image_info in layout_data.get("images", []):
                try:
                    page = pdf_doc[image_info["page_number"] - 1]
                    
                    # Extract image
                    img_data = self._extract_image(page, image_info["xref"])
                    
                    if img_data:
                        # Save image to disk
                        image_filename = f"doc_{document_id}_page_{image_info['page_number']}_img_{image_info['image_index']}.png"
                        image_path = self.images_dir / image_filename
                        
                        with open(image_path, "wb") as f:
                            f.write(img_data)
                        
                        # Extract any caption or nearby text
                        caption = self._extract_image_caption(page, image_info["bbox"])
                        
                        # Create database record
                        image_record = ImageData(
                            document_id=document_id,
                            image_path=str(image_path),
                            caption=caption,
                            page_number=image_info["page_number"],
                            bbox=image_info["bbox"],
                            image_type="extracted"
                        )
                        
                        db.add(image_record)
                        
                        extracted_images.append({
                            "image_path": str(image_path),
                            "caption": caption,
                            "page_number": image_info["page_number"]
                        })
                
                except Exception as e:
                    self.log_error(f"Error processing image: {str(e)}")
                    continue
            
            pdf_doc.close()
            db.commit()
        finally:
            db.close()
        
        self.log_info(f"Image extraction completed. Processed {len(extracted_images)} images")
        return extracted_images
    
    def _extract_image(self, page, xref: int) -> bytes:
        """Extract image data from PDF page"""
        try:
            base_image = page.parent.extract_image(xref)
            image_bytes = base_image["image"]
            return image_bytes
        except Exception as e:
            self.log_error(f"Error extracting image: {str(e)}")
            return None
    
    def _extract_image_caption(self, page, bbox: Dict) -> str:
        """Extract caption text near image"""
        try:
            # Look for text blocks near the image
            text_instances = page.get_text("dict")
            
            caption_texts = []
            
            for block in text_instances.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            span_bbox = span.get("bbox", [])
                            if self._is_near_image(span_bbox, bbox):
                                text = span.get("text", "").strip()
                                if text and ("figure" in text.lower() or "fig" in text.lower() or 
                                           "image" in text.lower() or "caption" in text.lower()):
                                    caption_texts.append(text)
            
            return " ".join(caption_texts[:3])  # Limit to first 3 potential captions
            
        except Exception as e:
            self.log_error(f"Error extracting caption: {str(e)}")
            return ""
    
    def _is_near_image(self, text_bbox: List, image_bbox: Dict, threshold: float = 50) -> bool:
        """Check if text is near image (within threshold pixels)"""
        if not text_bbox or len(text_bbox) < 4:
            return False
        
        # Calculate distance between text and image bounding boxes
        text_center_x = (text_bbox[0] + text_bbox[2]) / 2
        text_center_y = (text_bbox[1] + text_bbox[3]) / 2
        
        img_center_x = (image_bbox.get("x0", 0) + image_bbox.get("x1", 0)) / 2
        img_center_y = (image_bbox.get("y0", 0) + image_bbox.get("y1", 0)) / 2
        
        distance = ((text_center_x - img_center_x) ** 2 + (text_center_y - img_center_y) ** 2) ** 0.5
        
        return distance <= threshold