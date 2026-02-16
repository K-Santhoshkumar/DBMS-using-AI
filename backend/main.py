from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from db_manager import db_manager
from nlp_engine import nlp_engine
from sql_builder import sql_builder
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NLP to SQL API")

# Setup CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ConnectionRequest(BaseModel):
    db_type: str
    details: Dict[str, str]

class QueryRequest(BaseModel):
    natural_language_query: str

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    error: Optional[str] = None

# --- Routes ---

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.post("/connect")
def connect_database(request: ConnectionRequest):
    try:
        success = db_manager.connect(request.db_type, request.details)
        if success:
            return {"status": "success", "message": f"Connected to {request.db_type} database"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/schema")
def get_schema():
    try:
        schema = db_manager.get_schema()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def process_query(request: QueryRequest):
    try:
        # 1. Get Schema
        schema = db_manager.get_schema()
        
        # 2. Analyze Query with NLP
        nlp_analysis = nlp_engine.analyze_query(request.natural_language_query)
        
        # 3. Build SQL
        sql_query = sql_builder.build_sql(nlp_analysis, schema, db_type=db_manager.db_type)
        
        # 4. Check for errors in SQL generation
        if sql_query.startswith("ERROR"):
             return {
                "sql_query": sql_query,
                "results": [],
                "error": sql_query.replace("ERROR: ", "")
            }

        # 5. Execute SQL
        results = db_manager.execute_query(sql_query)
        
        return {
            "sql_query": sql_query,
            "results": results,
            "nlp_analysis": nlp_analysis # Optional: Return for debug/UI transparency
        }
        
    except Exception as e:
        # In a real app, don't expose raw errors
        return {
            "sql_query": "",
            "results": [],
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
