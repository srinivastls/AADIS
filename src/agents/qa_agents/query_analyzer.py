import re
from typing import Dict, List, Any
from src.agents.qa_agents.base_qa_agent import BaseQAAgent

class QueryAnalyzer(BaseQAAgent):
    """Analyzes user queries to determine intent and routing"""
    
    def __init__(self):
        super().__init__("QueryAnalyzer")
        self.capabilities = ["query_analysis", "intent_detection", "entity_extraction"]
        
        # Query patterns for different types
        self.text_patterns = [
            r'\b(what|who|when|where|why|how|explain|describe|tell me about)\b',
            r'\b(definition|meaning|concept|idea)\b',
            r'\b(summary|summarize|overview)\b'
        ]
        
        self.table_patterns = [
            r'\b(table|data|numbers|statistics|stats|values)\b',
            r'\b(row|column|cell|header)\b',
            r'\b(count|sum|average|total|maximum|minimum|mean)\b',
            r'\b(compare|comparison|versus|vs)\b',
            r'\b(list all|show all|find all)\b'
        ]
        
        self.image_patterns = [
            r'\b(image|picture|figure|chart|graph|diagram)\b',
            r'\b(visual|show|display|illustration)\b',
            r'\b(fig\.|figure \d+|image \d+)\b'
        ]
    
    def can_handle(self, query: str, query_type: str) -> bool:
        return True  # Query analyzer handles all queries
    
    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze query and determine routing strategy"""
        self.log_info(f"Analyzing query: {query}")
        
        query_lower = query.lower()
        
        # Determine query types
        query_types = []
        confidence_scores = {}
        
        # Check for text-based queries
        text_score = self._calculate_pattern_score(query_lower, self.text_patterns)
        if text_score > 0.3:
            query_types.append("text")
            confidence_scores["text"] = text_score
        
        # Check for table-based queries
        table_score = self._calculate_pattern_score(query_lower, self.table_patterns)
        if table_score > 0.3:
            query_types.append("table")
            confidence_scores["table"] = table_score
        
        # Check for image-based queries
        image_score = self._calculate_pattern_score(query_lower, self.image_patterns)
        if image_score > 0.3:
            query_types.append("image")
            confidence_scores["image"] = image_score
        
        # Default to text if no specific type detected
        if not query_types:
            query_types = ["text"]
            confidence_scores["text"] = 0.5
        
        # Extract entities and keywords
        entities = self._extract_entities(query)
        keywords = self._extract_keywords(query)
        
        analysis_result = {
            "original_query": query,
            "query_types": query_types,
            "confidence_scores": confidence_scores,
            "primary_type": max(confidence_scores.keys(), key=confidence_scores.get),
            "entities": entities,
            "keywords": keywords,
            "complexity": self._assess_complexity(query),
            "requires_multi_agent": len(query_types) > 1
        }
        
        self.log_info(f"Query analysis complete: {analysis_result}")
        return analysis_result
    
    def _calculate_pattern_score(self, query: str, patterns: List[str]) -> float:
        """Calculate how well query matches given patterns"""
        matches = 0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                matches += 1
        
        return matches / total_patterns if total_patterns > 0 else 0
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from query"""
        entities = []
        
        # Simple entity extraction patterns
        entity_patterns = [
            r'\b(table \d+|table \w+)\b',
            r'\b(figure \d+|fig\. \d+|image \d+)\b',
            r'\b(page \d+)\b',
            r'\b(chapter \d+|section \d+)\b'
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove stop words and extract meaningful terms
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'what', 'when', 'where', 'who',
            'why', 'how', 'can', 'could', 'should', 'would', 'do', 'does', 'did'
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Return top 10 keywords
    
    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        word_count = len(query.split())
        question_words = len(re.findall(r'\b(what|who|when|where|why|how)\b', query.lower()))
        
        if word_count > 20 or question_words > 2:
            return "high"
        elif word_count > 10 or question_words > 1:
            return "medium"
        else:
            return "low"
