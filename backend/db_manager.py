import os
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, inspect, text
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
            
            elif self.db_type == "mysql":
                user = connection_details.get("user")
                password = connection_details.get("password")
                host = connection_details.get("host", "localhost")
                port = connection_details.get("port", "3306")
                database = connection_details.get("database")
                connection_string = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"

            elif self.db_type == "postgresql":
                user = connection_details.get("user")
                password = connection_details.get("password")
                host = connection_details.get("host", "localhost")
                port = connection_details.get("port", "5432")
                database = connection_details.get("database")
                connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            elif self.db_type == "oracle":
                user = connection_details.get("user")
                password = connection_details.get("password")
                host = connection_details.get("host", "localhost")
                port = connection_details.get("port", "1521")
                service = connection_details.get("service")
                # Using thick mode or thin mode dependent on driver, using thin by default in modern oracledb
                connection_string = f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service}"

            else:
                raise ValueError(f"Unsupported database type: {db_type}")

            self.engine = create_engine(connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return True

        except Exception as e:
            print(f"Connection failed: {str(e)}")
            self.engine = None
            raise e

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
                column_details = [{
                    "name": col['name'], 
                    "type": str(col['type'])
                } for col in columns]
                
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

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a read-only SQL query and returns results as a list of dicts.
        """
        if not self.engine:
            raise ConnectionError("Database not connected")
        
        # Basic safety check (should be enhanced in validation layer)
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")

        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            keys = result.keys()
            return [dict(zip(keys, row)) for row in result.fetchall()]

# Global instance for simplicity in this project scope
db_manager = DBManager()
