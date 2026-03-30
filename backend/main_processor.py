import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from openai import OpenAI
import json

load_dotenv()

logger = logging.getLogger(__name__)

class SQLQueryProcessor:
    """Main class for processing natural language queries to SQL using OpenRouter"""
    
    def __init__(self, schema: Dict, db_type: str = "sqlite"):
        """
        Initialize the SQL Query Processor
        
        Args:
            schema: Database schema definition
            db_type: Database type (sqlite, postgresql, mysql, sqlserver)
        """
        self.schema = schema
        self.db_type = db_type
        self.conversation_history: List[Dict] = []
        
        logger.info(f"SQLQueryProcessor initialized with {len(schema)} tables, db_type={db_type}")

    def _format_schema(self) -> str:
        """Format the schema into a string prompt for OpenRouter API"""
        schema_parts = []
        for table_name, table_info in self.schema.items():
            columns = []
            for col in table_info.get("details", []):
                col_type = col.get("type", "unknown")
                columns.append(f"{col['name']} ({col_type})")
            
            pks = table_info.get("primary_keys", [])
            pk_str = f" Primary Keys: {pks}" if pks else ""
            
            fks = table_info.get("foreign_keys", [])
            fk_str = ""
            if fks:
                refs = [f"{fk['constrained_columns'][0]} -> {fk['referred_table']}({fk['referred_columns'][0]})" for fk in fks]
                fk_str = f" Foreign Keys: {', '.join(refs)}"
            
            schema_parts.append(f"Table {table_name}: Columns: [{', '.join(columns)}]{pk_str}{fk_str}")
        return "\n".join(schema_parts)

    def process_query(self, query: str, context: Optional[Dict] = None, mode: str = "query") -> Dict[str, Any]:
        """
        Process natural language query and return SQL
        
        Args:
            query: Natural language query
            context: Optional conversation context
            mode: 'query' for read-only, 'modification' for DDL/DML
            
        Returns:
            Dict with keys: sql, analysis, warnings, errors, success
        """
        result = {
            "sql": None,
            "analysis": {},
            "warnings": [],
            "errors": [],
            "success": False
        }
        
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            result["errors"].append("OpenRouter API Key is missing. Please provide a valid API key.")
            return result
        
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
            
            formatted_schema = self._format_schema()
            
            if mode == "query":
                instruction = (
                    f"You are a SQL expert for {self.db_type} databases. "
                    f"Write a valid, read-only SELECT SQL query based on the prompt below.\n"
                    f"IMPORTANT: You MUST ONLY generate SELECT statements. Data modification (INSERT, UPDATE, DELETE, DROP, ALTER, etc.) is STRICTLY PROHIBITED in this mode.\n"
                    f"If the user asks to modify data, return a SELECT statement that finds the data they are talking about instead, or return a harmless SELECT 1.\n"
                    f"Use only the provided schema. Respond ONLY with the raw SQL code, with no markdown formatting or explanation.\n"
                    f"Schema:\n{formatted_schema}"
                )
            else:
                db_warning = ""
                if self.db_type == "sqlite":
                    db_warning = "IMPORTANT: SQLite does NOT support User/Role management (CREATE ROLE, CREATE USER, GRANT, REVOKE). If the user asks for these or other unsupported features, you MUST respond EXACTLY with 'ERROR: SQLite does not support roles or permissions.' and nothing else.\n"
                
                instruction = (
                    f"You are a SQL expert for {self.db_type} databases. "
                    f"Write a valid DML/DDL SQL statement (INSERT, UPDATE, DELETE, CREATE, ALTER, etc.) based on the prompt below.\n"
                    f"Use the provided schema context. Respond ONLY with the raw SQL code, with no markdown formatting or explanation.\n"
                    f"{db_warning}"
                    f"Schema:\n{formatted_schema}"
                )
                        
            # Build messages array
            messages = [{"role": "system", "content": instruction}]
            
            # Keep history context
            if context and 'history' in context:
                for h in context['history']:
                    messages.append({"role": "user", "content": h['query']})
                    messages.append({"role": "assistant", "content": h['sql']})
            
            messages.append({"role": "user", "content": query})
            
            response = client.chat.completions.create(
                model="meta-llama/llama-3-8b-instruct",
                messages=messages
            )
            
            sql = response.choices[0].message.content.strip()
            
            # Clean up potential markdown formatting if the model still returns it
            if sql.startswith("```sql"):
                sql = sql[6:]
            elif sql.startswith("```"):
                sql = sql[3:]
            if sql.endswith("```"):
                sql = sql[:-3]
            
            sql = sql.strip()
            
            if sql.startswith("ERROR:"):
                result["errors"].append(sql)
                result["success"] = False
                return result
            
            result["sql"] = sql
            result["success"] = True
            
            # Simple analysis dict for frontend
            result["analysis"] = {
                "query_type": "Data Modification/DDL" if mode == "modification" else "Read-Only SELECT",
                "model_used": "OpenRouter (Llama 3 8B)",
                "mode": mode,
                "tables": list(self.schema.keys()) # just a proxy for now
            }
            
            self.conversation_history.append({
                "query": query,
                "sql": sql,
                "timestamp": datetime.now().isoformat()
            })
            if len(self.conversation_history) > 10:
                self.conversation_history.pop(0)
            
            logger.info("OpenRouter correctly generated SQL")
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"Error processing query with OpenRouter: {e}")
        
        return result
    
    def explain_query(self, query: str, mode: str = "query") -> str:
        """
        Generate explanation for the generated SQL using OpenRouter
        """
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            return "Please provide an OpenRouter API Key to explain the query."

        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
            
            formatted_schema = self._format_schema()
            prompt = (
                f"You are a helpful database assistant for a {self.db_type} database. "
                f"The user has asked: '{query}'. "
                f"Explain how you would write the SQL query for this using the schema below. "
                f"Keep it concise, formatting it nicely. \n\nSchema:\n{formatted_schema}"
            )
            response = client.chat.completions.create(
                model="meta-llama/llama-3-8b-instruct",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Failed to explain query: {str(e)}"

    def get_conversation_context(self, session_id: Optional[str] = None) -> Dict:
        return {"history": self.conversation_history}

    def clear_history(self):
        self.conversation_history = []
        logger.info("Conversation history cleared")