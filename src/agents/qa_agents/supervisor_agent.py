
from typing import Dict, List, Any, Optional
from src.agents.qa_agents.base_qa_agent import BaseQAAgent
from src.agents.qa_agents.query_analyzer import QueryAnalyzer
from src.agents.qa_agents.text_rag_agent import TextRAGAgent
from src.agents.qa_agents.table_analysis_agent import TableAnalysisAgent
from src.agents.qa_agents.image_analysis_agent import ImageAnalysisAgent

class SupervisorAgent(BaseQAAgent):
    """Supervisor agent that orchestrates multiple specialized agents"""
    
    def __init__(self):
        super().__init__("Supervisor")
        self.capabilities = ["query_routing", "agent_orchestration", "response_synthesis"]
        
        # Initialize specialized agents
        self.query_analyzer = QueryAnalyzer()
        self.text_rag_agent = TextRAGAgent()
        self.table_analysis_agent = TableAnalysisAgent()
        self.image_analysis_agent = ImageAnalysisAgent()
        
        # Agent registry
        self.agents = {
            "text": self.text_rag_agent,
            "table": self.table_analysis_agent,
            "image": self.image_analysis_agent
        }
        
        self.log_info("Supervisor agent initialized with all sub-agents")
    
    def can_handle(self, query: str, query_type: str) -> bool:
        return True  # Supervisor can handle all queries
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main entry point for processing user queries"""
        self.log_info(f"Supervisor processing query: {query}")
        
        try:
            # Step 1: Analyze the query
            analysis_result = self.query_analyzer.process_query(query, context or {})
            
            if analysis_result.get("status") == "error":
                return analysis_result
            
            # Step 2: Route to appropriate agents
            agent_results = self._route_to_agents(query, analysis_result)
            
            # Step 3: Synthesize responses
            final_response = self._synthesize_responses(query, analysis_result, agent_results)
            
            return final_response
            
        except Exception as e:
            self.log_error(f"Error in supervisor processing: {str(e)}")
            return {
                "status": "error",
                "message": f"Supervisor error: {str(e)}",
                "query": query
            }
    
    def _route_to_agents(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Route query to appropriate specialized agents"""
        query_types = analysis.get("query_types", ["text"])
        agent_results = {}
        
        self.log_info(f"Routing query to agents for types: {query_types}")
        
        # Process each query type
        for query_type in query_types:
            if query_type in self.agents:
                agent = self.agents[query_type]
                
                if agent.can_handle(query, query_type):
                    self.log_info(f"Processing with {agent.name} agent")
                    result = agent.process_query(query, analysis)
                    agent_results[query_type] = result
                else:
                    self.log_warning(f"Agent {agent.name} cannot handle query type {query_type}")
            else:
                self.log_warning(f"No agent available for query type: {query_type}")
        
        return agent_results
    
    def _synthesize_responses(self, query: str, analysis: Dict[str, Any], agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize responses from multiple agents into a coherent answer"""
        self.log_info("Synthesizing responses from agents")
        
        successful_results = {k: v for k, v in agent_results.items() if v.get("status") == "success"}
        
        if not successful_results:
            # No successful results
            error_messages = [v.get("message", "Unknown error") for v in agent_results.values() if v.get("status") == "error"]
            
            return {
                "status": "no_results",
                "message": "I couldn't find relevant information to answer your query. " + 
                          (f"Errors encountered: {'; '.join(error_messages)}" if error_messages else ""),
                "query": query,
                "analysis": analysis,
                "agent_results": agent_results
            }
        
        # Synthesize successful responses
        if len(successful_results) == 1:
            # Single agent response
            agent_type, result = next(iter(successful_results.items()))
            return {
                "status": "success",
                "answer": result["answer"],
                "sources": result["sources"],
                "query": query,
                "primary_agent": agent_type,
                "analysis": analysis
            }
        else:
            # Multi-agent response synthesis
            synthesized_answer = self._create_multi_agent_response(query, successful_results, analysis)
            all_sources = []
            
            for result in successful_results.values():
                all_sources.extend(result.get("sources", []))
            
            return {
                "status": "success",
                "answer": synthesized_answer,
                "sources": all_sources,
                "query": query,
                "agents_used": list(successful_results.keys()),
                "analysis": analysis,
                "multi_agent_response": True
            }
    
    def _create_multi_agent_response(self, query: str, results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Create a synthesized response from multiple agent results"""
        response = f"Based on your query '{query}', I found information from multiple sources:\n\n"
        
        # Order agents by relevance
        agent_order = ["text", "table", "image"]
        ordered_results = []
        
        for agent_type in agent_order:
            if agent_type in results:
                ordered_results.append((agent_type, results[agent_type]))
        
        # Add any remaining agents not in the predefined order
        for agent_type, result in results.items():
            if agent_type not in agent_order:
                ordered_results.append((agent_type, result))
        
        # Combine responses
        for i, (agent_type, result) in enumerate(ordered_results, 1):
            agent_name = agent_type.replace("_", " ").title()
            response += f"## {agent_name} Information:\n"
            response += f"{result['answer']}\n\n"
        
        response += "This comprehensive answer draws from multiple information sources in the documents."
        
        return response