from fastapi import FastAPI, HTTPException, Request, Depends, status
import uvicorn

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import traceback
import os

from db_manager import connection_pool
from main_processor import SQLQueryProcessor
from user_manager import user_manager, User, DBSession, QueryHistory
from auth import get_password_hash, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic Models for Auth
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class ConnectionRequest(BaseModel):
    db_type: str = Field(..., description="Database type (sqlite, postgresql, mysql, sqlserver)")
    details: Dict[str, str] = Field(..., description="Connection details")

class QueryRequest(BaseModel):
    natural_language_query: str
    mode: str = "query"
    db_session_id: int

class QueryResponse(BaseModel):
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

class ExplainRequest(BaseModel):
    natural_language_query: str
    db_session_id: int

class ExplainResponse(BaseModel):
    explanation: str
    sql_query: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

app = FastAPI(title="Hybrid NLP to SQL API with Neon DB", version="4.0.0")

# Configure CORS securely
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
origins = [url.strip() for url in frontend_url.split(",")] if frontend_url else ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Endpoints
@app.post("/auth/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(user_manager.get_db)):
    db_user_username = db.query(User).filter(User.username == user.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username, "user_id": new_user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(user_manager.get_db)):
    user = db.query(User).filter((User.username == form_data.username) | (User.email == form_data.username)).first()
    if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(user_manager.get_db)):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/auth/profile", response_model=UserProfile)
async def update_profile(update_data: UserUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(user_manager.get_db)):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if update_data.username:
        # Check if username is already taken by someone else
        existing_user = db.query(User).filter(User.username == update_data.username, User.id != user.id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = update_data.username
        
    if update_data.email:
        # Check if email is already taken by someone else
        existing_user = db.query(User).filter(User.email == update_data.email, User.id != user.id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already taken")
        user.email = update_data.email
        
    if update_data.password:
        user.password_hash = get_password_hash(update_data.password)
        
    db.commit()
    db.refresh(user)
    return user


# App Endpoints
@app.post("/connect")
async def connect_database(request: ConnectionRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(user_manager.get_db)):
    try:
        encrypted = user_manager.encrypt_dict(request.details)
        new_session = DBSession(
            user_id=current_user["user_id"],
            db_type=request.db_type,
            encrypted_details=encrypted
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        # Test connection immediately
        try:
            schema = connection_pool.get_schema(new_session.id)
            return {
                "status": "success",
                "message": f"Connected to {request.db_type} database",
                "db_session_id": new_session.id,
                "table_count": len(schema),
                "model_mode": "OpenRouter API integration active",
            }
        except Exception as conn_err:
            db.delete(new_session)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Connection failed: {str(conn_err)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_schema(db_session_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(user_manager.get_db)):
    try:
        session_record = db.query(DBSession).filter(DBSession.id == db_session_id, DBSession.user_id == current_user["user_id"]).first()
        if not session_record:
            raise HTTPException(status_code=404, detail="Database session not found or unauthorized")
            
        schema = connection_pool.get_schema(db_session_id)
        return {
            "database_type": session_record.db_type,
            "table_count": len(schema),
            "schema": schema,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(user_manager.get_db)):
    start_time = datetime.now()
    try:
        session_record = db.query(DBSession).filter(DBSession.id == request.db_session_id, DBSession.user_id == current_user["user_id"]).first()
        if not session_record:
            raise HTTPException(status_code=404, detail="Database session not found or unauthorized")
        
        schema = connection_pool.get_schema(request.db_session_id)
        processor = SQLQueryProcessor(schema=schema, db_type=session_record.db_type)
        
        # Build context from recent history
        past_queries = db.query(QueryHistory).filter(QueryHistory.session_id == request.db_session_id).order_by(QueryHistory.timestamp.desc()).limit(5).all()
        history_context = [{"query": q.nl_query, "sql": q.sql_query} for q in reversed(past_queries)]
        
        result = processor.process_query(request.natural_language_query, {"history": history_context}, mode=request.mode)
        
        if not result["success"]:
            error_msg = "; ".join(result["errors"])
            return QueryResponse(sql_query="", results=[], error=error_msg, nlp_analysis=result["analysis"], execution_time=(datetime.now() - start_time).total_seconds())

        sql_query = result["sql"]
        analysis = result["analysis"]
        row_count = 0
        execution_time = 0
        
        try:
            results = await connection_pool.execute_query_async(request.db_session_id, sql_query, mode=request.mode)
            execution_time = (datetime.now() - start_time).total_seconds()
            row_count = len(results)
            # Get DB name from session details
            try:
                details = user_manager.decrypt_dict(session_record.encrypted_details)
                db_name = details.get("database") or details.get("path", "").split("/")[-1] or session_record.db_type
            except:
                db_name = session_record.db_type

            # Record History
            qh = QueryHistory(
                user_id=current_user["user_id"],
                session_id=request.db_session_id,
                database_name=db_name,
                nl_query=request.natural_language_query,
                sql_query=sql_query,
                model_used=analysis.get("model_used"),
                execution_time=str(execution_time),
                row_count=row_count,
                success=True
            )
            db.add(qh)
            db.commit()
            
            if len(results) > 1000:
                results = results[:1000]
                analysis["warning"] = "Results truncated to 1000 rows"
                
            return QueryResponse(sql_query=sql_query, results=results, nlp_analysis=analysis, execution_time=execution_time, model_used=analysis.get("model_used"), session_id=str(request.db_session_id), row_count=row_count)

        except Exception as e:
            try:
                details = user_manager.decrypt_dict(session_record.encrypted_details)
                db_name = details.get("database") or details.get("path", "").split("/")[-1] or session_record.db_type
            except:
                db_name = session_record.db_type
                
            qh = QueryHistory(
                user_id=current_user["user_id"], session_id=request.db_session_id, database_name=db_name,
                nl_query=request.natural_language_query, sql_query=sql_query, success=False
            )
            db.add(qh)
            db.commit()
            return QueryResponse(sql_query=sql_query, results=[], error=str(e), nlp_analysis=analysis, execution_time=(datetime.now() - start_time).total_seconds())
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explain", response_model=ExplainResponse)
async def explain_query(request: ExplainRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(user_manager.get_db)):
    try:
        session_record = db.query(DBSession).filter(DBSession.id == request.db_session_id, DBSession.user_id == current_user["user_id"]).first()
        if not session_record:
            raise HTTPException(status_code=404, detail="Database session not found")
            
        schema = connection_pool.get_schema(request.db_session_id)
        processor = SQLQueryProcessor(schema=schema, db_type=session_record.db_type)
        
        explanation = processor.explain_query(request.natural_language_query)
        result = processor.process_query(request.natural_language_query, {}, mode="query")
        
        return ExplainResponse(
            explanation=explanation,
            sql_query=result["sql"] if result["success"] else None,
            analysis=result.get("analysis"),
            error="; ".join(result["errors"]) if not result["success"] else None
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/history/all")
async def get_all_history(current_user: dict = Depends(get_current_user), db: Session = Depends(user_manager.get_db), limit: int = 100):
    try:
        history = db.query(QueryHistory).filter(QueryHistory.user_id == current_user["user_id"]).order_by(QueryHistory.timestamp.desc()).limit(limit).all()
        return {
            "query_count": len(history),
            "history": [{"query": h.nl_query, "sql": h.sql_query, "database_name": h.database_name, "timestamp": h.timestamp.isoformat(), "success": h.success, "execution_time": h.execution_time, "row_count": h.row_count, "model_used": h.model_used} for h in history]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/history/{db_session_id}")
async def get_history(db_session_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(user_manager.get_db), limit: int = 50):
    try:
        history = db.query(QueryHistory).filter(QueryHistory.session_id == db_session_id, QueryHistory.user_id == current_user["user_id"]).order_by(QueryHistory.timestamp.desc()).limit(limit).all()
        return {
            "session_id": str(db_session_id),
            "query_count": len(history),
            "history": [{"query": h.nl_query, "sql": h.sql_query, "database_name": h.database_name, "timestamp": h.timestamp.isoformat(), "success": h.success} for h in history]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
