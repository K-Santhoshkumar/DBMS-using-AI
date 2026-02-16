from nlp_engine import nlp_engine
from sql_builder import sql_builder
from db_manager import db_manager

try:
    db_manager.connect("sqlite", {"path": "sample.db"}) 
    schema = db_manager.get_schema()
    q = "give the records name,id,salary from departments and employees table salary by highest"
    print(f"Query: {q}")
    analysis = nlp_engine.analyze_query(q)
    print(f"Analysis: {analysis}")
    sql = sql_builder.build_sql(analysis, schema)
    print(f"SQL: {sql}")
except Exception as e:
    print(f"Error: {e}")
