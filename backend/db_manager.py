from typing import Dict, List, Any, Optional
import urllib.parse
from sqlalchemy import create_engine, inspect, text, URL
from sqlalchemy.engine import Engine

class DBManager:
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.db_type: Optional[str] = None

    def connect(self, db_type: str, connection_details: Dict[str, str]) -> bool:
        """
        Establishes a database connection based on type and details.
        """
        self.db_type = db_type.lower()
        connection_string = ""

        try:
            if self.db_type == "sqlite":
                # For SQLite, path is the file path
                db_path = connection_details.get("path", "sample.db")
                connection_string = f"sqlite:///{db_path}"
            
            else:
                user = connection_details.get("user", "").strip() or None
                password = connection_details.get("password", "") or None
                
                # Validate required credentials
                if self.db_type in ["mysql", "postgresql"]:
                    if not user or not password:
                        raise ValueError(f"{self.db_type.capitalize()} requires both 'user' and 'password' to be provided.")
                
                host = connection_details.get("host", "localhost").strip() or "localhost"
                
                # Prevent psycopg2 from defaulting to IPv6 (::1) on Windows, which often causes auth issues
                if host.lower() == "localhost" and self.db_type == "postgresql":
                    host = "127.0.0.1"
                
                # Resolve port safely
                port_str = connection_details.get("port")
                port = None
                
                try:
                    if self.db_type == "mysql":
                        drivername = "mysql+mysqlconnector"
                        port = int(port_str) if port_str else 3306
                    elif self.db_type == "postgresql":
                        drivername = "postgresql"
                        port = int(port_str) if port_str else 5432
                    else:
                        raise ValueError(f"Unsupported database type: {self.db_type}")
                except ValueError as ve:
                    # Catch ValueError from int() if port_str is garbled
                    if "invalid literal" in str(ve).lower():
                        raise ValueError(f"Invalid port number provided: '{port_str}'")
                    raise ve
                
                database = connection_details.get("database", "").strip() or None
                
                query = {}
                
                connection_string = URL.create(
                    drivername=drivername,
                    username=user,
                    password=password,
                    host=host,
                    port=port,
                    database=database,
                    query=query
                )
                
                # Print debug visibility safely
                print(f"DEBUG: Attempting connection to {drivername}://{user}:***@{host}:{port}/{database}")

            self.engine = create_engine(connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return True

        except Exception as e:
            print(f"Connection failed: {str(e)}")
            self.engine = None
            raise e

    def disconnect(self):
        """
        Closes the database engine gracefully.
        """
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.db_type = None
            print("DEBUG: Database disconnected.")

    def get_schema(self) -> Dict[str, List[str]]:
        """
        Introspects the database to get tables and columns.
        Returns: {table_name: [column_names]}
        """
        if not self.engine:
            raise ConnectionError("Database not connected")

        inspector = inspect(self.engine)
        schema_info = {}

        try:
            table_names = inspector.get_table_names()
            for table in table_names:
                # Get Columns
                columns = inspector.get_columns(table)
                column_details = []
                for col in columns:
                    try:
                        col_type = str(col['type'])
                    except Exception:
                         col_type = "UNKNOWN"
                    column_details.append({
                        "name": col['name'],
                        "type": col_type
                    })
                
                # Get Primary Keys
                pk_constraint = inspector.get_pk_constraint(table)
                pks = pk_constraint.get('constrained_columns', [])

                # Get Foreign Keys
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

    def execute_query(self, query: str, mode: str = "query") -> List[Dict[str, Any]]:
        """
        Executes a SQL query and returns results as a list of dicts.
        If mode is 'modification', it allows DML/DDL and commits.
        """
        if not self.engine:
            raise ConnectionError("Database not connected")
        
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

            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                keys = result.keys()
                return [dict(zip(keys, row)) for row in result.fetchall()]
        
        elif mode == "modification":
            # For DML/DDL operations
            if self.db_type == "sqlite":
                with self.engine.connect() as conn:
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
                with self.engine.connect() as conn:
                    with conn.begin(): # implicit commit
                        result = conn.execute(text(query))
                        if result.returns_rows:
                            keys = result.keys()
                            return [dict(zip(keys, row)) for row in result.fetchall()]
                        else:
                            return [{"message": f"Query executed successfully. Rows affected: {result.rowcount}"}]
        else:
            raise ValueError(f"Unknown mode: {mode}")

# Global instance for simplicity in this project scope
db_manager = DBManager()
