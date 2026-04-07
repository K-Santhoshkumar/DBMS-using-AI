from typing import Dict, List, Any, Optional
import urllib.parse
from sqlalchemy import create_engine, inspect, text, URL
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import Engine
import threading
from user_manager import user_manager, DBSession

class ConnectionPoolManager:
    def __init__(self):
        self.connections: Dict[int, Engine] = {}
        self.lock = threading.Lock()

    def get_or_create_engine(self, db_session_id: int) -> Engine:
        with self.lock:
            if db_session_id in self.connections:
                return self.connections[db_session_id]

        # Cache miss, fetch from Neon DB
        db = next(user_manager.get_db())
        session_record = db.query(DBSession).filter(DBSession.id == db_session_id).first()
        
        if not session_record:
            raise ValueError("Database session not found or expired.")
            
        details = user_manager.decrypt_dict(session_record.encrypted_details)
        db_type = session_record.db_type
        
        connection_string = ""
        
        import os
        
        if db_type == "sqlite":
            raw_path = details.get("path", "sample.db")
            # SSRF/Path Traversal Protection: Extract just the filename
            filename = os.path.basename(raw_path)
            if not filename or filename == "." or filename == "..":
                filename = "sample.db"
                
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, filename)
            connection_string = f"sqlite:///{db_path}"
        else:
            user = details.get("user", "").strip() or None
            password = details.get("password", "") or None
            host = details.get("host", "localhost").strip() or "localhost"
            
            # SSRF Protection: Prevent connections to local network unless explicitly allowed by environment
            allow_local = os.getenv("ALLOW_LOCAL_DB", "true").lower() == "true"
            forbidden_hosts = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
            
            if not allow_local:
                # Basic check for localhost aliases that could map to internal metadata or db
                if host.lower() in forbidden_hosts or host.startswith("169.254."):
                    raise ValueError("Connections to local or internal loopback addresses are restricted for security.")
            
            if host.lower() == "localhost" and db_type == "postgresql":
                host = "127.0.0.1"
                
            port_str = details.get("port")
            port = None
            if port_str:
                port = int(port_str)
            else:
                if db_type == "mysql": port = 3306
                elif db_type == "postgresql": port = 5432
                elif db_type == "sqlserver": port = 1433
                
            drivername = db_type
            if db_type == "mysql": drivername = "mysql+mysqlconnector"
            
            database = details.get("database", "").strip() or None
            
            query = {}
            if host and "neon.tech" in host:
                query = {"sslmode": "require"}
            
            connection_string = URL.create(
                drivername=drivername,
                username=user,
                password=password,
                host=host,
                port=port,
                database=database,
                query=query
            )
            
        connect_args = {}
        if db_type == "postgresql":
            connect_args = {
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }

        engine = create_engine(
            connection_string,
            connect_args=connect_args,
            poolclass=NullPool,
            pool_reset_on_return=None
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
        with self.lock:
            self.connections[db_session_id] = engine
            return engine

    def remove_engine(self, db_session_id: int):
        with self.lock:
            if db_session_id in self.connections:
                self.connections[db_session_id].dispose()
                del self.connections[db_session_id]

    def get_schema(self, db_session_id: int) -> Dict[str, List[str]]:
        engine = self.get_or_create_engine(db_session_id)
        inspector = inspect(engine)
        schema_info = {}

        try:
            table_names = inspector.get_table_names()
            for table in table_names:
                columns = inspector.get_columns(table)
                column_details = []
                for col in columns:
                    try:
                        col_type = str(col['type'])
                    except:
                         col_type = "UNKNOWN"
                    column_details.append({
                        "name": col['name'],
                        "type": col_type
                    })
                
                pk_constraint = inspector.get_pk_constraint(table)
                pks = pk_constraint.get('constrained_columns', [])

                fks = inspector.get_foreign_keys(table)
                fk_details = [{
                    "constrained_columns": fk['constrained_columns'],
                    "referred_table": fk['referred_table'],
                    "referred_columns": fk['referred_columns']
                } for fk in fks]

                schema_info[table] = {
                    "columns": [c['name'] for c in column_details],
                    "details": column_details,
                    "primary_keys": pks,
                    "foreign_keys": fk_details
                }
            return schema_info
        except Exception as e:
            print(f"Schema introspection failed: {str(e)}")
            raise e

    def _execute_sync(self, engine: Engine, query: str, mode: str, db_type: str) -> List[Dict[str, Any]]:
        import re
        query_upper = query.strip().upper()

        if mode == "query":
            if not (query_upper.startswith("SELECT") or query_upper.startswith("EXPLAIN") or query_upper.startswith("WITH")):
                raise ValueError("Only SELECT queries (or CTEs) are allowed in Querying mode.")

            forbidden_keywords = [
                "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", 
                "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE"
            ]
            for kw in forbidden_keywords:
                if re.search(fr'\b{kw}\b', query_upper):
                    raise ValueError(f"Data manipulation not allowed in Querying mode. Found restricted keyword: {kw}")

            with engine.connect() as conn:
                result = conn.execute(text(query))
                try:
                    keys = result.keys()
                    return [dict(zip(keys, row)) for row in result.fetchall()]
                except Exception:
                    return [{"message":"Executed successfully but return unparsable results."}]
        
        elif mode == "modification":
            if db_type == "sqlite":
                with engine.connect() as conn:
                    dbapi_conn = conn.connection.driver_connection
                    cursor = dbapi_conn.cursor()
                    try:
                        cursor.executescript(query)
                        dbapi_conn.commit()
                        return [{"message": "Query executed successfully."}]
                    except Exception as e:
                        dbapi_conn.rollback()
                        raise e
                    finally:
                        cursor.close()
            else:
                with engine.connect() as conn:
                    with conn.begin(): # implicit commit
                        result = conn.execute(text(query))
                        if result.returns_rows:
                            keys = result.keys()
                            return [dict(zip(keys, row)) for row in result.fetchall()]
                        else:
                            return [{"message": f"Query executed successfully. Rows affected: {result.rowcount}"}]
        else:
            raise ValueError(f"Unknown mode: {mode}")

    async def execute_query_async(self, db_session_id: int, query: str, mode: str = "query") -> List[Dict[str, Any]]:
        engine = self.get_or_create_engine(db_session_id)
        
        db = next(user_manager.get_db())
        session_record = db.query(DBSession).filter(DBSession.id == db_session_id).first()
        db_type = session_record.db_type if session_record else "unknown"
        
        from fastapi.concurrency import run_in_threadpool
        return await run_in_threadpool(self._execute_sync, engine, query, mode, db_type)

connection_pool = ConnectionPoolManager()
