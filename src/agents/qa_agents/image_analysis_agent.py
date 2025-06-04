
from typing import Dict, List, Any, Optional
from src.agents.qa_agents.base_qa_agent import BaseQAAgent
from src.database.connection import db_manager
from src.models.document_models import ImageData, Document

class ImageAnalysisAgent(BaseQAAgent):
    """Agent for analyzing and querying image data"""
    
    def __init__(self):
        super().__init__("ImageAnalysis")
        self.capabilities = ["image_query", "caption_search", "image_retrieval"]
    
    def can_handle(self, query: str, query_type: str) -> bool:
        return query_type == "image"
    
    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process image-related queries"""
        self.log_info(f"Processing image query: {query}")
        
        try:
            # Find relevant images
            relevant_images = self._find_relevant_images(query, context)
            
            if not relevant_images:
                return {
                    "status": "no_results",
                    "message": "No relevant images found for your query.",
                    "sources": []
                }
            
            # Analyze images based on query
            analysis_results = []
            for image in relevant_images:
                result = self._analyze_image(query, image)
                if result:
                    analysis_results.append(result)
            
            if not analysis_results:
                return {
                    "status": "no_results",
                    "message": "Could not extract meaningful information from the images.",
                    "sources": []
                }
            
            # Combine results
            answer = self._combine_image_results(query, analysis_results)
            sources = self._format_image_sources(relevant_images)
            
            return {
                "status": "success",
                "answer": answer,
                "sources": sources,
                "images_analyzed": len(relevant_images),
                "agent_type": "image_analysis"
            }
            
        except Exception as e:
            self.log_error(f"Error processing image query: {str(e)}")
            return {
                "status": "error",
                "message": f"Error analyzing images: {str(e)}",
                "sources": []
            }
    
    def _find_relevant_images(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find images relevant to the query"""
        try:
            with next(db_manager.get_db_session()) as db:
                images = db.query(ImageData).all()
                
                relevant_images = []
                query_lower = query.lower()
                keywords = context.get("keywords", [])
                entities = context.get("entities", [])
                
                for image in images:
                    relevance_score = 0
                    
                    # Check caption relevance
                    if image.caption:
                        caption_lower = image.caption.lower()
                        for keyword in keywords:
                            if keyword in caption_lower:
                                relevance_score += 2
                        
                        # Check for figure references
                        for entity in entities:
                            if entity.lower() in caption_lower:
                                relevance_score += 3
                    
                    # Check alt text relevance
                    if image.alt_text:
                        alt_text_lower = image.alt_text.lower()
                        for keyword in keywords:
                            if keyword in alt_text_lower:
                                relevance_score += 1
                    
                    # Check for specific figure references in query
                    if any(ref in query_lower for ref in ['figure', 'fig', 'image', 'picture']):
                        relevance_score += 1
                    
                    if relevance_score > 0:
                        document = db.query(Document).filter(Document.id == image.document_id).first()
                        relevant_images.append({
                            "image_data": image,
                            "document": document,
                            "relevance_score": relevance_score
                        })
                
                # Sort by relevance
                relevant_images.sort(key=lambda x: x['relevance_score'], reverse=True)
                
                self.log_info(f"Found {len(relevant_images)} relevant images")
                return relevant_images[:5]  # Return top 5 images
                
        except Exception as e:
            self.log_error(f"Error finding relevant images: {str(e)}")
            return []

    
    def _analyze_image(self, query: str, image_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze individual image for query"""
        try:
            image_data = image_info["image_data"]
            document = image_info["document"]
            
            query_lower = query.lower()
            
            # Basic image analysis based on available metadata
            analysis = {
                "image_path": image_data.image_path,
                "caption": image_data.caption or "No caption available",
                "alt_text": image_data.alt_text or "No alt text available",
                "width": image_data.width,
                "height": image_data.height,
                "document_name": document.filename if document else "Unknown",
                "page_number": image_data.page_number
            }
            
            # Generate response based on query type
            if any(word in query_lower for word in ['show', 'display', 'what is', 'describe']):
                analysis["response"] = f"Image from page {image_data.page_number}: {image_data.caption or 'Image without caption'}"
            elif any(word in query_lower for word in ['caption', 'title']):
                analysis["response"] = f"Caption: {image_data.caption or 'No caption available'}"
            elif any(word in query_lower for word in ['size', 'dimensions']):
                analysis["response"] = f"Image dimensions: {image_data.width}x{image_data.height} pixels"
            else:
                analysis["response"] = f"Image information: {image_data.caption or 'Image from page ' + str(image_data.page_number)}"
            
            return analysis
            
        except Exception as e:
            self.log_error(f"Error analyzing image: {str(e)}")
            return None
    
    def _combine_image_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Combine results from multiple images"""
        answer = f"Based on the image analysis for your query '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            answer += f"Image {i} (from {result['document_name']}, Page {result['page_number']}):\n"
            answer += f"Caption: {result['caption']}\n"
            answer += f"Analysis: {result['response']}\n\n"
        
        return answer
    
    def _format_image_sources(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format image source information"""
        sources = []
        for image_info in images:
            image_data = image_info["image_data"]
            document = image_info["document"]
            
            sources.append({
                "type": "image",
                "document": document.filename if document else "Unknown",
                "page": image_data.page_number,
                "caption": image_data.caption or "No caption",
                "path": image_data.image_path,
                "dimensions": f"{image_data.width}x{image_data.height}" if image_data.width and image_data.height else "Unknown",
                "relevance": image_info["relevance_score"]
            })
        
        return sources
