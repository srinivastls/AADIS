
import streamlit as st
import json
from typing import Dict, Any
from src.qa_system.qa_orchestrator import QAOrchestrator

class WebInterface:
    """Streamlit web interface for the QA system"""
    
    def __init__(self):
        self.orchestrator = None
    
    def initialize_orchestrator(self):
        """Initialize orchestrator with caching"""
        if self.orchestrator is None:
            self.orchestrator = QAOrchestrator()
        return self.orchestrator
    
    def run(self):
        """Run the Streamlit interface"""
        st.set_page_config(
            page_title="Agentic Document Intelligence QA",
            page_icon="🤖",
            layout="wide"
        )
        
        st.title("🤖 Agentic Document Intelligence QA System")
        st.markdown("Ask questions about your documents and get intelligent answers from multiple specialized agents.")
        
        # Initialize session state
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        
        if 'orchestrator' not in st.session_state:
            st.session_state.orchestrator = self.initialize_orchestrator()
        
        # Sidebar
        with st.sidebar:
            st.header("System Information")
            st.info("This system uses multiple specialized agents to analyze documents and answer your questions.")
            
            st.header("Available Agents")
            st.write("🔍 **Query Analyzer**: Understands your questions")
            st.write("📝 **Text RAG Agent**: Answers from text content")
            st.write("📊 **Table Analysis Agent**: Analyzes tabular data")
            st.write("🖼️ **Image Analysis Agent**: Processes images and figures")
            st.write("🎯 **Supervisor Agent**: Orchestrates all agents")
            
            if st.button("Clear Conversation"):
                st.session_state.conversation_history = []
                st.session_state.orchestrator.clear_history("web_session")
                st.success("Conversation cleared!")
        
        # Main interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("Ask Your Question")
            
            # Question input
            question = st.text_area(
                "Enter your question about the documents:",
                height=100,
                placeholder="e.g., What are the main findings in Table 1? Or, Summarize the conclusions from the research paper."
            )
            
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                ask_button = st.button("Ask Question", type="primary")
            
            # Process question
            if ask_button and question.strip():
                with st.spinner("Processing your question..."):
                    response = st.session_state.orchestrator.ask_question(question, "web_session")
                    
                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        "question": question,
                        "response": response
                    })
        
        with col2:
            st.header("Quick Examples")
            example_questions = [
                "What are the key findings?",
                "Show me data from tables",
                "What images are available?",
                "Summarize the main points",
                "What statistics are mentioned?"
            ]
            
            for example in example_questions:
                if st.button(example, key=f"example_{example}"):
                    st.session_state.example_question = example
        
        # Display conversation
        if st.session_state.conversation_history:
            st.header("Conversation")
            
            for i, entry in enumerate(reversed(st.session_state.conversation_history)):
                with st.expander(f"Q: {entry['question'][:50]}...", expanded=(i == 0)):
                    st.write("**Question:**", entry['question'])
                    st.write("**Answer:**", entry['response']['answer'])
                    
                    # Show sources
                    if entry['response'].get('sources'):
                        st.write("**Sources:**")
                        for j, source in enumerate(entry['response']['sources'], 1):
                            source_info = f"{j}. {source['document']} (Page {source['page']}) - {source['type']}"
                            if source.get('description'):
                                source_info += f"\n   {source['description']}"
                            st.text(source_info)
                    
                    # Show metadata
                    if entry['response'].get('query_type'):
                        st.caption(f"Query Type: {entry['response']['query_type']} | "
                                 f"Confidence: {entry['response'].get('confidence', 'unknown')}")

def run_streamlit_app():
    """Run the Streamlit app"""
    web_interface = WebInterface()
    web_interface.run()

if __name__ == "__main__":
    run_streamlit_app()