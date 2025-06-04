
from typing import Dict, List, Any, Optional
from src.agents.qa_agents.base_qa_agent import BaseQAAgent
from src.database.connection import db_manager
from src.models.document_models import TableData, Document
import pandas as pd
import re
import json
import numpy as np

class TableAnalysisAgent(BaseQAAgent):
    """Agent for analyzing and querying table data"""
    
    def __init__(self):
        super().__init__("TableAnalysis")
        self.capabilities = ["table_query", "data_analysis", "table_search"]
    
    def can_handle(self, query: str, query_type: str) -> bool:
        return query_type == "table"
    
    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process table-related queries"""
        self.log_info(f"Processing table query: {query}")
        
        try:
            # Find relevant tables
            relevant_tables = self._find_relevant_tables(query, context)
            
            if not relevant_tables:
                return {
                    "status": "no_results",
                    "message": "No relevant tables found for your query.",
                    "sources": []
                }
            
            # Analyze tables based on query
            analysis_results = []
            for table in relevant_tables:
                result = self._analyze_table(query, table)
                if result:
                    analysis_results.append(result)
            
            if not analysis_results:
                return {
                    "status": "no_results",
                    "message": "Could not extract meaningful information from the tables.",
                    "sources": []
                }
            
            # Combine results
            answer = self._combine_table_results(query, analysis_results)
            sources = self._format_table_sources(relevant_tables)
            
            return {
                "status": "success",
                "answer": answer,
                "sources": sources,
                "tables_analyzed": len(relevant_tables),
                "agent_type": "table_analysis"
            }
            
        except Exception as e:
            self.log_error(f"Error processing table query: {str(e)}")
            return {
                "status": "error",
                "message": f"Error analyzing tables: {str(e)}",
                "sources": []
            }
    
    def _find_relevant_tables(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find tables relevant to the query"""
        try:
            with next(db_manager.get_db_session()) as db:
                tables = db.query(TableData).all()
                
                relevant_tables = []
                query_lower = query.lower()
                keywords = context.get("keywords", [])
                
                for table in tables:
                    relevance_score = 0
                    
                    # Check caption relevance
                    if table.caption:
                        caption_lower = table.caption.lower()
                        for keyword in keywords:
                            if keyword in caption_lower:
                                relevance_score += 1
                    
                    # Check headers relevance
                    if table.headers:
                        headers_text = " ".join(table.headers).lower()
                        for keyword in keywords:
                            if keyword in headers_text:
                                relevance_score += 2
                    
                    # Check table data relevance
                    if table.table_data and isinstance(table.table_data, dict):
                        table_text = json.dumps(table.table_data).lower()
                        for keyword in keywords:
                            if keyword in table_text:
                                relevance_score += 1
                    
                    if relevance_score > 0:
                        document = db.query(Document).filter(Document.id == table.document_id).first()
                        relevant_tables.append({
                            "table_data": table,
                            "document": document,
                            "relevance_score": relevance_score
                        })
                
                # Sort by relevance
                relevant_tables.sort(key=lambda x: x['relevance_score'], reverse=True)
                
                self.log_info(f"Found {len(relevant_tables)} relevant tables")
                return relevant_tables[:5]  # Return top 5 tables
                
        except Exception as e:
            self.log_error(f"Error finding relevant tables: {str(e)}")
            return []
    
    def _analyze_table(self, query: str, table_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze individual table for query"""
        try:
            table_data = table_info["table_data"]
            document = table_info["document"]
            
            if not table_data.table_data:
                return None
            
            # Convert to DataFrame if possible
            df = self._convert_to_dataframe(table_data.table_data)
            if df is None:
                return None
            
            query_lower = query.lower()
            
            # Determine analysis type
            if any(word in query_lower for word in ['count', 'how many', 'number of']):
                result = self._count_analysis(df, query)
            elif any(word in query_lower for word in ['sum', 'total', 'add']):
                result = self._sum_analysis(df, query)
            elif any(word in query_lower for word in ['average', 'mean']):
                result = self._average_analysis(df, query)
            elif any(word in query_lower for word in ['maximum', 'max', 'highest']):
                result = self._max_analysis(df, query)
            elif any(word in query_lower for word in ['minimum', 'min', 'lowest']):
                result = self._min_analysis(df, query)
            elif any(word in query_lower for word in ['list', 'show', 'find']):
                result = self._list_analysis(df, query)
            else:
                result = self._general_analysis(df, query)
            
            if result:
                result.update({
                    "document_name": document.filename if document else "Unknown",
                    "page_number": table_data.page_number,
                    "table_caption": table_data.caption or "No caption",
                    "table_headers": table_data.headers or []
                })
            
            return result
            
        except Exception as e:
            self.log_error(f"Error analyzing table: {str(e)}")
            return None
    
    def _convert_to_dataframe(self, table_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Convert table data to pandas DataFrame"""
        try:
            if 'data' in table_data and isinstance(table_data['data'], list):
                df = pd.DataFrame(table_data['data'])
                return df
            elif 'rows' in table_data and 'headers' in table_data:
                df = pd.DataFrame(table_data['rows'], columns=table_data['headers'])
                return df
            else:
                return None
        except Exception as e:
            self.log_error(f"Error converting to DataFrame: {str(e)}")
            return None
    
    def _count_analysis(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Perform count analysis on DataFrame"""
        return {
            "analysis_type": "count",
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "summary": f"This table contains {len(df)} rows and {len(df.columns)} columns."
        }
    
    def _sum_analysis(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Perform sum analysis on DataFrame"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            sums = df[numeric_columns].sum()
            return {
                "analysis_type": "sum",
                "numeric_sums": sums.to_dict(),
                "summary": f"Sums calculated for numeric columns: {', '.join(numeric_columns)}"
            }
        return {
            "analysis_type": "sum",
            "summary": "No numeric columns found for sum calculation."
        }
    
    def _average_analysis(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Perform average analysis on DataFrame"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            averages = df[numeric_columns].mean()
            return {
                "analysis_type": "average",
                "numeric_averages": averages.to_dict(),
                "summary": f"Averages calculated for numeric columns: {', '.join(numeric_columns)}"
            }
        return {
            "analysis_type": "average",
            "summary": "No numeric columns found for average calculation."
        }
    
    def _max_analysis(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Perform maximum analysis on DataFrame"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            maxima = df[numeric_columns].max()
            return {
                "analysis_type": "maximum",
                "numeric_maxima": maxima.to_dict(),
                "summary": f"Maximum values found for numeric columns: {', '.join(numeric_columns)}"
            }
        return {
            "analysis_type": "maximum",
            "summary": "No numeric columns found for maximum calculation."
        }
    
    def _min_analysis(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Perform minimum analysis on DataFrame"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            minima = df[numeric_columns].min()
            return {
                "analysis_type": "minimum",
                "numeric_minima": minima.to_dict(),
                "summary": f"Minimum values found for numeric columns: {', '.join(numeric_columns)}"
            }
        return {
            "analysis_type": "minimum",
            "summary": "No numeric columns found for minimum calculation."
        }
    
    def _list_analysis(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Perform list analysis on DataFrame"""
        return {
            "analysis_type": "list",
            "columns": df.columns.tolist(),
            "sample_data": df.head(5).to_dict('records'),
            "summary": f"Table has columns: {', '.join(df.columns)}"
        }
    
    def _general_analysis(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Perform general analysis on DataFrame"""
        return {
            "analysis_type": "general",
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": df.columns.tolist(),
            "data_types": df.dtypes.to_dict(),
            "summary": f"General table information: {len(df)} rows, {len(df.columns)} columns"
        }
    
    def _combine_table_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Combine results from multiple tables"""
        answer = f"Based on the table analysis for your query '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            answer += f"Table {i} (from {result['document_name']}, Page {result['page_number']}):\n"
            answer += f"Caption: {result['table_caption']}\n"
            answer += f"Analysis: {result['summary']}\n\n"
        
        return answer
    
    def _format_table_sources(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format table source information"""
        sources = []
        for table_info in tables:
            table_data = table_info["table_data"]
            document = table_info["document"]
            
            sources.append({
                "type": "table",
                "document": document.filename if document else "Unknown",
                "page": table_data.page_number,
                "caption": table_data.caption or "No caption",
                "headers": table_data.headers or [],
                "relevance": table_info["relevance_score"]
            })
        
        return sources