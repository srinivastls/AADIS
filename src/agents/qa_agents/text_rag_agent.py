
from typing import Dict, List, Any, Optional
from src.agents.qa_agents.base_qa_agent import BaseQAAgent
from src.database.connection import db_manager
from src.models.document_models import TextBlock, Document
import numpy as np

class TextRAGAgent(BaseQAAgent):
    """RAG agent for text-based queries"""
    
    def __init__(self):
        super().__init__("TextRAG")
        self.capabilities = ["text_retrieval", "semantic_search", "text_qa"]
        self.top_k = 5
    
    def can_handle(self, query: str, query_type: str) -> bool:
        return query_type in ["text", "general"]
    
    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process text-based queries using RAG"""
        self.log_info(f"Processing text query: {query}")
        
        try:
            # Retrieve relevant text chunks
            relevant_chunks = self._retrieve_relevant_texts(query, context)
            
            if not relevant_chunks:
                return {
                    "status": "no_results",
                    "message": "No relevant text found for your query.",
                    "sources": []
                }
            
            # Generate answer using retrieved context
            answer = self._generate_answer(query, relevant_chunks)
            
            # Format sources
            sources = self._format_sources(relevant_chunks)
            
            return {
                "status": "success",
                "answer": answer,
                "sources": sources,
                "retrieved_chunks": len(relevant_chunks),
                "agent_type": "text_rag"
            }
            
        except Exception as e:
            self.log_error(f"Error processing text query: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing query: {str(e)}",
                "sources": []
            }
    
    def _retrieve_relevant_texts(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve relevant text chunks using semantic search"""
        try:
            # Query vector database
            query_embedding = db_manager.embedding_model.encode([query])
            
            results = db_manager.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=self.top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            relevant_chunks = []
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Get additional info from database
                    with next(db_manager.get_db_session()) as db:
                        text_block = db.query(TextBlock).filter(
                            TextBlock.document_id == metadata['document_id'],
                            TextBlock.page_number == metadata['page_number']
                        ).first()
                        
                        if text_block:
                            document = db.query(Document).filter(
                                Document.id == text_block.document_id
                            ).first()
                            
                            relevant_chunks.append({
                                "content": doc,
                                "metadata": metadata,
                                "similarity_score": 1 - distance,  # Convert distance to similarity
                                "document_name": document.filename if document else "Unknown",
                                "page_number": metadata.get('page_number', 1),
                                "block_type": metadata.get('block_type', 'text')
                            })
            
            # Sort by similarity score
            relevant_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            self.log_info(f"Retrieved {len(relevant_chunks)} relevant text chunks")
            return relevant_chunks
            
        except Exception as e:
            self.log_error(f"Error retrieving texts: {str(e)}")
            return []
    
    def _generate_answer(self, query: str, relevant_chunks: List[Dict[str, Any]]) -> str:
        """Generate answer using retrieved context"""
        # Combine relevant contexts
        context_text = "\n\n".join([
            f"[From {chunk['document_name']}, Page {chunk['page_number']}]\n{chunk['content']}"
            for chunk in relevant_chunks[:3]  # Use top 3 chunks
        ])
        
        # Simple template-based answer generation
        # In a real implementation, you'd use an LLM here
        if len(context_text.strip()) > 0:
            # For now, return a structured response
            answer = f"Based on the documents, here's what I found:\n\n"
            
            for i, chunk in enumerate(relevant_chunks[:3], 1):
                answer += f"{i}. From {chunk['document_name']} (Page {chunk['page_number']}):\n"
                answer += f"   {chunk['content'][:200]}...\n\n"
            
            answer += f"This information addresses your query: '{query}'"
        else:
            answer = "I couldn't find specific information to answer your query in the available documents."
        
        return answer
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source information"""
        sources = []
        for chunk in chunks:
            sources.append({
                "document": chunk['document_name'],
                "page": chunk['page_number'],
                "type": chunk['block_type'],
                "similarity": round(chunk['similarity_score'], 3),
                "snippet": chunk['content'][:150] + "..." if len(chunk['content']) > 150 else chunk['content']
            })
        return sources