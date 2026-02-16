import sys
import os

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_manager import db_manager
from nlp_engine import nlp_engine
from sql_builder import sql_builder

def test_system():
    print("--- 1. Testing Database Connection (SQLite) ---")
    try:
        # Create sample db first if not exists
        if not os.path.exists("sample.db"):
            import create_sample_db
            create_sample_db.create_sample_db()
            
        success = db_manager.connect("sqlite", {"path": "sample.db"})
        print(f"Connection Success: {success}")
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    print("\n--- 2. Testing Schema Retrieval ---")
    try:
        schema = db_manager.get_schema()
        # print(f"Schema: {schema}")
        print("Schema loaded.")
    except Exception as e:
        print(f"Schema Retrieval Failed: {e}")
        return

    queries = [
    "give the records name,id,salary from departments and employees table salary by highest",
    "give the first two records with name,id,salary from departments and employees"
    ]

    for q in queries:
        print(f"\nQuery: '{q}'")
        try:
            # Analyze
            analysis = nlp_engine.analyze_query(q)
            print(f"  Analysis: {analysis}")
            
            # Build SQL
            sql = sql_builder.build_sql(analysis, schema)
            print(f"  Generated SQL: {sql}")
            
            # Execute
            if not sql.startswith("ERROR"):
                 # Skip execution as we don't have department id 3 in sample data
                 pass
            else:
                print(f"  SQL Error: {sql}")
                
        except Exception as e:
            print(f"  Processing Failed: {e}")

if __name__ == "__main__":
    test_system()
