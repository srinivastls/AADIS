#!/usr/bin/env python3
"""
Unified Main Entry Point for the Agentic Document Intelligence System
Supports both Phase 1 (Document Processing) and Phase 2 (QA System)
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging(log_level="INFO"):
    """Setup logging configuration"""
    from config.settings import settings
    
    settings.LOGS_DIR.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.LOGS_DIR / 'agentic_system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_document_processing(args):
    """Run Phase 1 - Document Processing"""
    from src.agents.coordinator import DocumentProcessingCoordinator
    from config.settings import settings
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Agentic Document Intelligence System - Phase 1 (Document Processing)")
    
    # Initialize coordinator
    coordinator = DocumentProcessingCoordinator()
    
    if args.file:
        # Process single file
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
        
        try:
            results = coordinator.process_document(str(file_path))
            logger.info(f"Successfully processed: {file_path}")
            logger.info(f"Results: {results['summary']}")
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")
    
    else:
        # Process all files in input directory
        input_dir = Path(args.input_dir or settings.INPUT_DIR)
        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return
        
        # Supported file types
        supported_extensions = ['.pdf', '.docx', '.doc']
        files_to_process = []
        
        for ext in supported_extensions:
            files_to_process.extend(input_dir.glob(f"*{ext}"))
        
        if not files_to_process:
            logger.warning(f"No supported documents found in {input_dir}")
            return
        
        logger.info(f"Found {len(files_to_process)} documents to process")
        
        # Process each document
        successful = 0
        failed = 0
        
        for file_path in files_to_process:
            try:
                logger.info(f"Processing: {file_path.name}")
                results = coordinator.process_document(str(file_path))
                logger.info(f"✓ Successfully processed: {file_path.name}")
                logger.info(f"  Summary: {results['summary']}")
                successful += 1
            except Exception as e:
                logger.error(f"✗ Failed to process {file_path.name}: {str(e)}")
                failed += 1
        
        logger.info(f"Processing completed. Success: {successful}, Failed: {failed}")

def run_qa_cli(args):
    """Run Phase 2 - QA CLI Interface"""
    from src.interfaces.cli_interface import CLIInterface
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Agentic Document Intelligence System - Phase 2 (QA CLI)")
    
    cli = CLIInterface()
    
    if args.question:
        # Single question mode
        response = cli.ask_single_question(args.question)
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(response, f, indent=2)
            print(f"Response saved to {args.output}")
        else:
            cli._display_response(response)
    else:
        # Interactive mode
        cli.run_interactive_mode()

def run_qa_web(args):
    """Run Phase 2 - QA Web Interface"""
    logger = logging.getLogger(__name__)
    logger.info("Starting Agentic Document Intelligence System - Phase 2 (QA Web)")
    
    try:
        import streamlit as st
        from src.interfaces.web_interface import run_streamlit_app
        
        # Set Streamlit configuration
        os.environ['STREAMLIT_SERVER_PORT'] = str(args.port)
        os.environ['STREAMLIT_SERVER_ADDRESS'] = args.host
        
        print(f"Starting Streamlit web interface at http://{args.host}:{args.port}")
        run_streamlit_app()
        
    except ImportError:
        logger.error("Streamlit not installed. Install with: pip install streamlit")
        sys.exit(1)

def run_qa_api(args):
    """Run Phase 2 - QA API Interface"""
    logger = logging.getLogger(__name__)
    logger.info("Starting Agentic Document Intelligence System - Phase 2 (QA API)")
    
    try:
        import uvicorn
        from src.interfaces.api_interface import app
        
        print(f"Starting FastAPI server at http://{args.host}:{args.port}")
        print(f"API documentation available at http://{args.host}:{args.port}/docs")
        
        uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())
        
    except ImportError:
        logger.error("FastAPI/Uvicorn not installed. Install with: pip install fastapi uvicorn")
        sys.exit(1)

def run_full_pipeline(args):
    """Run complete pipeline - Process documents then start QA system"""
    logger = logging.getLogger(__name__)
    logger.info("Starting Full Pipeline - Document Processing + QA System")
    
    # Step 1: Process documents
    logger.info("Step 1: Processing documents...")
    run_document_processing(args)
    
    # Step 2: Start QA system
    logger.info("Step 2: Starting QA system...")
    if args.qa_interface == "web":
        run_qa_web(args)
    elif args.qa_interface == "api":
        run_qa_api(args)
    else:
        run_qa_cli(args)

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='Agentic Document Intelligence System - Unified Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Phase 1 - Document Processing
  python main.py process --input-dir ./documents
  python main.py process --file ./document.pdf
  
  # Phase 2 - QA System
  python main.py qa-cli --interactive
  python main.py qa-cli --question "What are the main findings?"
  python main.py qa-web --port 8501
  python main.py qa-api --port 8000
  
  # Full Pipeline
  python main.py pipeline --input-dir ./documents --qa-interface web
        """
    )
    
    # Global arguments
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Phase 1 - Document Processing
    process_parser = subparsers.add_parser('process', help='Process documents (Phase 1)')
    process_parser.add_argument('--input-dir', type=str, help='Input directory containing documents')
    process_parser.add_argument('--file', type=str, help='Process a single file')
    
    # Phase 2 - QA CLI
    qa_cli_parser = subparsers.add_parser('qa-cli', help='QA system CLI interface (Phase 2)')
    qa_cli_parser.add_argument('--question', '-q', type=str, help='Ask a single question')
    qa_cli_parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    qa_cli_parser.add_argument('--output', '-o', type=str, help='Output file for single question (JSON)')
    
    # Phase 2 - QA Web
    qa_web_parser = subparsers.add_parser('qa-web', help='QA system web interface (Phase 2)')
    qa_web_parser.add_argument('--port', type=int, default=8501, help='Port for web interface')
    qa_web_parser.add_argument('--host', type=str, default='localhost', help='Host for web interface')
    
    # Phase 2 - QA API
    qa_api_parser = subparsers.add_parser('qa-api', help='QA system API interface (Phase 2)')
    qa_api_parser.add_argument('--port', type=int, default=8000, help='Port for API interface')
    qa_api_parser.add_argument('--host', type=str, default='0.0.0.0', help='Host for API interface')
    
    # Full Pipeline
    pipeline_parser = subparsers.add_parser('pipeline', help='Full pipeline - Process + QA (Both Phases)')
    pipeline_parser.add_argument('--input-dir', type=str, help='Input directory containing documents')
    pipeline_parser.add_argument('--file', type=str, help='Process a single file')
    pipeline_parser.add_argument('--qa-interface', choices=['cli', 'web', 'api'], default='cli',
                                help='QA interface to start after processing')
    pipeline_parser.add_argument('--port', type=int, default=8501, help='Port for web/api interface')
    pipeline_parser.add_argument('--host', type=str, default='localhost', help='Host for web/api interface')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Handle no command (default to interactive CLI)
    if not args.command:
        print("No command specified. Starting interactive QA CLI...")
        args.command = 'qa-cli'
        args.interactive = True
    
    # Route to appropriate function
    try:
        if args.command == 'process':
            run_document_processing(args)
        elif args.command == 'qa-cli':
            run_qa_cli(args)
        elif args.command == 'qa-web':
            run_qa_web(args)
        elif args.command == 'qa-api':
            run_qa_api(args)
        elif args.command == 'pipeline':
            run_full_pipeline(args)
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error: {str(e)}")
        if args.log_level == 'DEBUG':
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()