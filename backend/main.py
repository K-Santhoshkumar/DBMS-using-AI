"""
FastAPI Application for Natural Language to SQL Conversion
Provides REST API endpoints for database connection and query processing
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
import uuid
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules from split architecture
try:
    from db_manager import db_manager
    from main_processor import SQLQueryProcessor
    logger.info("Successfully imported modules from split architecture")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Please ensure nlp_engine.py, sql_builder.py, main_processor.py, and db_manager.py exist")
    raise

# ============================================================================
# Pydantic Models
# ============================================================================

class ConnectionRequest(BaseModel):
    """Request model for database connection"""
    db_type: str = Field(..., description="Database type (sqlite, postgresql, mysql, sqlserver)")
    details: Dict[str, str] = Field(..., description="Connection details (host, port, database, user, password)")

class QueryRequest(BaseModel):
    """Request model for natural language query"""
    natural_language_query: str = Field(..., description="Natural language query to convert to SQL")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    mode: str = Field("query", description="Mode: 'query' or 'modification'")

class QueryResponse(BaseModel):
    """Response model for query processing"""
    model_config = {"protected_namespaces": ()}
    sql_query: str
    results: List[Dict[str, Any]]
    error: Optional[str] = None
    nlp_analysis: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    model_used: Optional[str] = None
    session_id: Optional[str] = None
    warnings: Optional[List[str]] = None
    row_count: Optional[int] = None

class FeedbackRequest(BaseModel):
    """Request model for feedback submission"""
    session_id: str
    query: str
    generated_sql: str
    corrected_sql: str
    feedback: str

class ModelInfoResponse(BaseModel):
    """Response model for model information"""
    t5_loaded: bool
    spacy_loaded: bool
    device: Optional[str]
    mode: str
    engine_initialized: bool
    available_models: List[str]

class ExplainRequest(BaseModel):
    """Request model for query explanation"""
    natural_language_query: str = Field(..., description="Natural language query to explain")
    session_id: Optional[str] = Field(None, description="Session ID for context")

class ExplainResponse(BaseModel):
    """Response model for query explanation"""
    explanation: str
    sql_query: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SessionInfo(BaseModel):
    """Response model for session information"""
    session_id: str
    query_count: int
    last_query: Optional[str] = None
    last_sql: Optional[str] = None
    timestamp: Optional[str] = None
    context: Dict[str, Any]

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str
    components: Dict[str, bool]
    statistics: Dict[str, Any]

# ============================================================================
# Application Setup
# ============================================================================

app = FastAPI(
    title="Hybrid NLP to SQL API",
    description="Convert natural language to SQL using T5 + spaCy hybrid approach",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Global State Management
# ============================================================================

class ApplicationState:
    """Manages application state"""
    def __init__(self):
        self.processor = None
        self.conversation_contexts = {}
        self.query_history = []
        self.feedback_log = []
    
    def get_processor(self):
        """Get the SQL query processor"""
        return self.processor
    
    def set_processor(self, processor):
        """Set the SQL query processor"""
        self.processor = processor
    
    def get_context(self, session_id: str) -> Dict:
        """Get conversation context for a session"""
        return self.conversation_contexts.get(session_id, {})
    
    def set_context(self, session_id: str, context: Dict):
        """Set conversation context for a session"""
        self.conversation_contexts[session_id] = context
    
    def add_to_history(self, entry: Dict):
        """Add an entry to query history"""
        self.query_history.append(entry)
        # Keep only last 1000 entries
        if len(self.query_history) > 1000:
            self.query_history.pop(0)
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get query history for a session"""
        return [q for q in self.query_history if q.get("session_id") == session_id]
    
    def clear_session(self, session_id: str):
        """Clear session data"""
        if session_id in self.conversation_contexts:
            del self.conversation_contexts[session_id]
        self.query_history = [q for q in self.query_history if q.get("session_id") != session_id]
    
    def add_feedback(self, feedback: Dict):
        """Add feedback entry"""
        self.feedback_log.append(feedback)
        # Keep only last 500 feedback entries
        if len(self.feedback_log) > 500:
            self.feedback_log.pop(0)

# Initialize application state
app_state = ApplicationState()

# ============================================================================
# Helper Functions
# ============================================================================



# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def read_root():
    """Root endpoint with API information"""
    return {
        "status": "Hybrid NLP to SQL API is running",
        "version": "3.0.0",
        "architecture": "Split Architecture (NLP Engine + SQL Builder + Main Processor)",
        "components": {
            "openrouter": True,
            "database": db_manager.engine is not None if db_manager else False
        },
        "features": [
            "OpenRouter API for text-to-SQL generation",
            "Read-only and Data Modification modes",
            "Multiple database support (SQLite, PostgreSQL, MySQL, SQL Server)",
            "Conversation context management",
            "Query explanation",
            "Query history tracking",
            "Session management",
            "Feedback collection"
        ],
        "endpoints": {
            "GET /": "API information",
            "POST /connect": "Connect to database",
            "POST /query": "Process natural language query",
            "POST /explain": "Explain SQL query",
            "GET /schema": "Get database schema",
            "GET /history/{session_id}": "Get query history",
            "DELETE /history/{session_id}": "Clear session history",
            "GET /model-info": "Get model information",
            "GET /stats": "Get system statistics",
            "GET /health": "Health check",
            "POST /feedback": "Submit feedback"
        },
        "documentation": "/docs"
    }

@app.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get model information"""
    t5_loaded = False
    device = None
    
    return {
        "t5_loaded": False,
        "spacy_loaded": False,
        "device": "cloud",
        "mode": "OpenRouter API",
        "engine_initialized": app_state.processor is not None,
        "available_models": [
            "OpenRouter Models"
        ]
    }

@app.post("/connect")
async def connect_database(request: ConnectionRequest):
    """Connect to database and initialize NLP engine"""
    try:
        logger.info(f"Connecting to {request.db_type} database...")
        
        # Connect to database
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not available")
        
        success = db_manager.connect(request.db_type, request.details)
        
        if not success:
            raise HTTPException(status_code=400, detail="Connection failed - please check credentials")
        
        # Get schema
        schema = db_manager.get_schema()
        
        if not schema:
            raise HTTPException(status_code=400, detail="No tables found in database")
        
        # Create processor with schema
        processor = SQLQueryProcessor(
            schema=schema,
            db_type=db_manager.db_type
        )
        
        app_state.set_processor(processor)
        
        # Prepare schema summary
        schema_summary = {}
        for table_name, table_info in schema.items():
            schema_summary[table_name] = {
                "columns": table_info.get("columns", []),
                "column_count": len(table_info.get("columns", [])),
                "has_foreign_keys": len(table_info.get("foreign_keys", [])) > 0
            }
        
        logger.info(f"Successfully connected to {request.db_type}. Found {len(schema)} tables")
        
        return {
            "status": "success",
            "message": f"Connected to {request.db_type} database",
            "database_type": request.db_type,
            "schema": schema_summary,
            "table_count": len(schema),
            "total_columns": sum(len(info.get("columns", [])) for info in schema.values()),
            "model_mode": "OpenRouter API integration active",
            "connection_details": {
                "host": request.details.get("host", "localhost"),
                "database": request.details.get("database", request.details.get("dbname", "unknown"))
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Connection error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@app.get("/schema")
async def get_schema():
    """Get detailed database schema"""
    try:
        if not db_manager or not db_manager.engine:
            raise HTTPException(status_code=400, detail="Database not connected")
        
        schema = db_manager.get_schema()
        
        # Format schema with details
        formatted_schema = {}
        total_columns = 0
        
        for table_name, table_info in schema.items():
            columns = table_info.get("columns", [])
            total_columns += len(columns)
            
            formatted_schema[table_name] = {
                "columns": columns,
                "column_count": len(columns),
                "details": table_info.get("details", []),
                "foreign_keys": table_info.get("foreign_keys", []),
                "primary_keys": table_info.get("primary_keys", [])
            }
        
        return {
            "database_type": db_manager.db_type,
            "table_count": len(schema),
            "total_columns": total_columns,
            "schema": formatted_schema,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process natural language query to SQL and execute"""
    start_time = datetime.now()
    
    try:
        # Validate connection
        if not db_manager or not db_manager.engine:
            raise HTTPException(status_code=400, detail="Database not connected. Please connect first.")
        
        # Validate processor
        if not app_state.get_processor():
            raise HTTPException(status_code=400, detail="NLP engine not initialized. Please connect to database first.")
        
        processor = app_state.get_processor()
        
        # Session management
        session_id = request.session_id or str(uuid.uuid4())
        context = app_state.get_context(session_id)
        
        logger.info(f"Processing query using OpenRouter: {request.natural_language_query[:100]}...")
        
        # Process query
        result = processor.process_query(
            request.natural_language_query, 
            context,
            mode=request.mode
        )
        
        if not result["success"]:
            error_msg = "; ".join(result["errors"]) if result["errors"] else "Query processing failed"
            logger.error(f"Query processing failed: {error_msg}")
            
            return QueryResponse(
                sql_query="",
                results=[],
                error=error_msg,
                nlp_analysis=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                model_used=None,
                session_id=session_id,
                warnings=result["warnings"]
            )
        
        analysis = result["analysis"]
        sql_query = result["sql"]
        
        # Convert analysis to dictionary
        analysis_dict = analysis
        
        # Execute SQL query
        try:
            results = db_manager.execute_query(sql_query, mode=request.mode)
            execution_time = (datetime.now() - start_time).total_seconds()
            row_count = len(results)
            
            # Refresh backend schema for OpenRouter context if data definition might have changed
            if request.mode == "modification":
                updated_schema = db_manager.get_schema()
                processor.schema = updated_schema
                logger.info("Auto-refreshed backend schema context after Data Modification query.")
            
            logger.info(f"Query executed successfully in {execution_time:.2f}s, {row_count} rows returned")
            
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return QueryResponse(
                sql_query=sql_query,
                results=[],
                error=f"Query execution failed: {str(e)}",
                nlp_analysis=analysis_dict,
                execution_time=(datetime.now() - start_time).total_seconds(),
                model_used=analysis.get("model_used", "openrouter"),
                session_id=session_id,
                warnings=analysis.get("warnings", [])
            )
        
        # Update context for conversation
        app_state.set_context(session_id, {
            "last_query": request.natural_language_query,
            "last_sql": sql_query,
            "last_tables": analysis.get("tables", []),
            "query_count": app_state.get_context(session_id).get("query_count", 0) + 1,
            "timestamp": datetime.now().isoformat()
        })
        
        # Store in history
        app_state.add_to_history({
            "session_id": session_id,
            "query": request.natural_language_query,
            "sql": sql_query,
            "model": analysis.get("model_used", "openrouter"),
            "row_count": row_count,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "success": True
        })
        
        # Limit results for response (max 1000 rows)
        if len(results) > 1000:
            results = results[:1000]
            analysis_dict["warning"] = "Results truncated to 1000 rows"
        
        return QueryResponse(
            sql_query=sql_query,
            results=results,
            nlp_analysis=analysis_dict,
            execution_time=execution_time,
            model_used=analysis.get("model_used", "openrouter"),
            session_id=session_id,
            warnings=analysis.get("warnings", []),
            row_count=row_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/explain", response_model=ExplainResponse)
async def explain_query(request: ExplainRequest):
    """Explain the generated SQL for a natural language query"""
    try:
        # Validate connection
        if not db_manager or not db_manager.engine:
            raise HTTPException(status_code=400, detail="Database not connected")
        
        # Validate processor
        if not app_state.get_processor():
            raise HTTPException(status_code=400, detail="NLP engine not initialized")
        
        processor = app_state.get_processor()
        
        # Get context
        session_id = request.session_id or str(uuid.uuid4())
        context = app_state.get_context(session_id)
        
        # Get explanation
        explanation = processor.explain_query(request.natural_language_query)
        
        # Also get the SQL and analysis
        result = processor.process_query(request.natural_language_query, context)
        
        analysis_dict = None
        if result["success"]:
            analysis_dict = result["analysis"]
        
        return ExplainResponse(
            explanation=explanation,
            sql_query=result["sql"] if result["success"] else None,
            analysis=analysis_dict,
            error="; ".join(result["errors"]) if not result["success"] else None
        )
        
    except Exception as e:
        logger.error(f"Error explaining query: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for system improvement"""
    try:
        feedback_data = {
            "feedback_id": str(uuid.uuid4()),
            "session_id": request.session_id,
            "query": request.query,
            "generated_sql": request.generated_sql,
            "corrected_sql": request.corrected_sql,
            "feedback": request.feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store feedback
        app_state.add_feedback(feedback_data)
        
        logger.info(f"Feedback received: {feedback_data['feedback_id']} - {request.feedback[:100]}")
        
        return {
            "status": "success",
            "message": "Thank you for your feedback! It will help improve the system.",
            "feedback_id": feedback_data["feedback_id"],
            "timestamp": feedback_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    """Get query history for a session"""
    try:
        session_history = app_state.get_session_history(session_id)
        
        # Sort by timestamp (newest first)
        session_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply limit
        if limit and limit > 0:
            session_history = session_history[:min(limit, 100)]
        
        context = app_state.get_context(session_id)
        
        return SessionInfo(
            session_id=session_id,
            query_count=len(session_history),
            last_query=context.get("last_query"),
            last_sql=context.get("last_sql"),
            timestamp=context.get("timestamp"),
            context={
                "query_count": context.get("query_count", 0),
                "last_tables": context.get("last_tables", []),
                "last_columns_count": len(context.get("last_columns", []))
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear query history for a session"""
    try:
        app_state.clear_session(session_id)
        
        return {
            "status": "success",
            "message": f"History cleared for session {session_id}",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        # Calculate statistics
        total_queries = len(app_state.query_history)
        
        if total_queries > 0:
            # Model usage statistics
            model_usage = {}
            for q in app_state.query_history:
                model = q.get("model", "unknown")
                model_usage[model] = model_usage.get(model, 0) + 1
            
            # Average execution time
            exec_times = [q.get("execution_time", 0) for q in app_state.query_history if q.get("execution_time")]
            avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
            
            # Success rate
            success_count = sum(1 for q in app_state.query_history if q.get("success", False))
            success_rate = (success_count / total_queries) * 100 if total_queries > 0 else 0
            
            # Top tables accessed
            table_usage = {}
            for q in app_state.query_history:
                if "analysis" in q and hasattr(q["analysis"], "tables"):
                    for table in q["analysis"].tables:
                        table_usage[table] = table_usage.get(table, 0) + 1
            
            top_tables = sorted(table_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        else:
            model_usage = {}
            avg_exec_time = 0
            success_rate = 0
            top_tables = []
        
        return {
            "total_queries": total_queries,
            "active_sessions": len(app_state.conversation_contexts),
            "total_feedback": len(app_state.feedback_log),
            "model_usage": model_usage,
            "performance": {
                "average_execution_time_ms": avg_exec_time * 1000,
                "success_rate_percent": round(success_rate, 2),
                "fastest_query_ms": min([q.get("execution_time", 0) * 1000 for q in app_state.query_history if q.get("execution_time")], default=0),
                "slowest_query_ms": max([q.get("execution_time", 0) * 1000 for q in app_state.query_history if q.get("execution_time")], default=0)
            },
            "top_tables": [{"table": table, "queries": count} for table, count in top_tables],
            "database_connected": db_manager and db_manager.engine is not None,
            "nlp_engine_initialized": app_state.processor is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check database connection
        db_connected = db_manager and db_manager.engine is not None
        if db_connected:
            try:
                # Test query
                db_manager.execute_query("SELECT 1")
                db_healthy = True
            except:
                db_healthy = False
        else:
            db_healthy = False
        
        # Check NLP engine
        nlp_ready = app_state.processor is not None
        
        # Check T5 model
        t5_loaded = nlp_ready and app_state.processor.nlp_engine.use_pretrained
        
        return HealthResponse(
            status="healthy" if (db_healthy and nlp_ready) else "degraded",
            timestamp=datetime.now().isoformat(),
            components={
                "database": db_connected,
                "database_healthy": db_healthy,
                "nlp_engine": nlp_ready,
                "t5_model": t5_loaded,
                "spacy_model": True
            },
            statistics={
                "queries_processed": len(app_state.query_history),
                "active_sessions": len(app_state.conversation_contexts),
                "feedback_received": len(app_state.feedback_log),
                "tables_available": len(db_manager.get_schema()) if db_connected else 0
            }
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            components={"error": True},
            statistics={"error": str(e)}
        )

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down API...")
    if db_manager and db_manager.engine:
        try:
            db_manager.disconnect()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
    
    logger.info("API shutdown complete")

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 Hybrid NLP to SQL API v3.0.0")
    print("=" * 70)
    print("📚 Architecture: Split Architecture (NLP Engine + SQL Builder + Main Processor)")
    print("🔧 Components:")
    print("   • main_processor - OpenRouter API orchestration")
    print("   • Database Manager - Multi-database support")
    print("")
    print("🌐 API Documentation:")
    print("   • Swagger UI: http://localhost:8000/docs")
    print("   • ReDoc: http://localhost:8000/redoc")
    print("")
    print("📡 Server starting on http://localhost:8000")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
        reload=False  # Set to True for development
    )