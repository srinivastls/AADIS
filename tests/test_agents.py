import unittest
import tempfile
import os
from pathlib import Path
from src.agents.layout_analyzer import LayoutAnalyzerAgent
from src.agents.text_extractor import TextExtractionAgent
from src.agents.coordinator import DocumentProcessingCoordinator

class TestAgents(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
       
    def test_layout_analyzer_agent(self):
        """Test layout analyzer agent initialization"""
        agent = LayoutAnalyzerAgent()
        self.assertEqual(agent.name, "LayoutAnalyzer")
        self.assertIsNotNone(agent.converter)
    
    def test_text_extractor_agent(self):
        """Test text extractor agent initialization"""
        agent = TextExtractionAgent()
        self.assertEqual(agent.name, "TextExtractor")
    
    def test_coordinator_initialization(self):
        """Test coordinator initialization with all agents"""
        coordinator = DocumentProcessingCoordinator()
        self.assertEqual(coordinator.name, "Coordinator")
        self.assertIsNotNone(coordinator.layout_analyzer)
        self.assertIsNotNone(coordinator.text_extractor)
        self.assertIsNotNone(coordinator.table_extractor)
        self.assertIsNotNone(coordinator.image_processor)

if __name__ == '__main__':
    unittest.main()