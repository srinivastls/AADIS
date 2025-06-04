
from typing import Dict, Any, Optional, List
import logging
from src.agents.qa_agents.supervisor_agent import SupervisorAgent
from src.database.connection import db_manager

class QAOrchestrator:
    """Main orchestrator for the QA system"""
    
    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.conversation_history = []
        self.logger = logging.getLogger(__name__)
    
    def ask_question(self, question: str, session_id: str = "default") -> Dict[str, Any]:
        """Main interface for asking questions"""
        self.logger.info(f"Processing question: {question}")
        
        try:
            # Process the question through supervisor
            response = self.supervisor.process_query(question)
            
            # Store in conversation history
            conversation_entry = {
                "session_id": session_id,
                "question": question,
                "response": response,
                "timestamp": self._get_timestamp()
            }
            
            self.conversation_history.append(conversation_entry)
            
            # Format response for user
            formatted_response = self._format_user_response(response)
            
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error processing question: {str(e)}")
            return {
                "status": "error",
                "message": f"I encountered an error while processing your question: {str(e)}",
                "question": question
            }
    
    def get_conversation_history(self, session_id: str = "default") -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return [entry for entry in self.conversation_history if entry["session_id"] == session_id]
    
    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session"""
        self.conversation_history = [
            entry for entry in self.conversation_history 
            if entry["session_id"] != session_id
        ]
    
    def _format_user_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Format response for end user"""
        if response.get("status") == "success":
            formatted = {
                "answer": response["answer"],
                "sources": self._format_sources_for_user(response.get("sources", [])),
                "confidence": "high" if response.get("multi_agent_response") else "medium"
            }
            
            # Add analysis info if available
            if "analysis" in response:
                formatted["query_type"] = response["analysis"].get("primary_type", "unknown")
                formatted["complexity"] = response["analysis"].get("complexity", "unknown")
        
        elif response.get("status") == "no_results":
            formatted = {
                "answer": "I couldn't find specific information to answer your question in the available documents.",
                "suggestion": "Try rephrasing your question or asking about different aspects of the documents.",
                "sources": []
            }
        
        else:  # error status
            formatted = {
                "answer": "I encountered an error while processing your question.",
                "error": response.get("message", "Unknown error"),
                "sources": []
            }
        
        return formatted
    
    def _format_sources_for_user(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources in a user-friendly way"""
        formatted_sources = []
        
        for source in sources:
            formatted_source = {
                "document": source.get("document", "Unknown"),
                "page": source.get("page", "Unknown"),
                "type": source.get("type", "text")
            }
            
            # Add type-specific information
            if source.get("type") == "table":
                if source.get("caption"):
                    formatted_source["description"] = f"Table: {source['caption']}"
                if source.get("headers"):
                    formatted_source["columns"] = source["headers"]
            
            elif source.get("type") == "image":
                if source.get("caption"):
                    formatted_source["description"] = f"Image: {source['caption']}"
                if source.get("dimensions"):
                    formatted_source["size"] = source["dimensions"]
            
            else:  # text
                if source.get("snippet"):
                    formatted_source["preview"] = source["snippet"]
            
            formatted_sources.append(formatted_source)
        
        return formatted_sources
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()