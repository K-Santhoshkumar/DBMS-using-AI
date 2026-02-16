from typing import Dict, List, Any, Optional
import re

class SQLBuilder:
    def build_sql(self, analysis: Dict[str, Any], schema: Dict[str, List[str]], db_type: str = "sqlite") -> str:
        """
        Generates SQL (Deterministic Structured Version)
        """
        tables = analysis.get("tables", [])
        columns = analysis.get("columns", [])
        conditions = analysis.get("conditions", [])
        logic = analysis.get("logic", "AND")
        join_type = analysis.get("join_type", "JOIN")
        aggregate = analysis.get("aggregate")
        group_by = analysis.get("group_by")
        having = analysis.get("having", [])
        order_col = analysis.get("order_by_col")
        order_dir = analysis.get("order_dir", "ASC")
        limit = analysis.get("limit")
        offset = analysis.get("offset")

        # --------------------------
        # Resolve Tables
        # --------------------------
        resolved_tables = []
        for t in tables:
            for s in schema.keys():
                # check if user input matches schema, OR if schema is part of user input (e.g. "employees table")
                if t.lower() == s.lower() or t.lower() in s.lower() or s.lower() in t.lower():
                     if s not in resolved_tables: resolved_tables.append(s)
                     
        if not resolved_tables:
             if len(schema) > 0:
                 # Auto-detect from columns if implicit?
                 # For now, fallback to first table
                 resolved_tables = [list(schema.keys())[0]]
             else:
                 return "ERROR: No tables found."

        main_table = resolved_tables[0]

        # --------------------------
        # JOIN
        # --------------------------
        from_clause = main_table
        joined_set = {main_table}

        for t in resolved_tables[1:]:
            if t in joined_set: continue
            
            joined = False
            # Check FK main -> t
            for fk in schema[main_table].get("foreign_keys", []):
                if fk["referred_table"] == t:
                    col_source = fk['constrained_columns'][0]
                    col_target = fk['referred_columns'][0]
                    from_clause += f" {join_type} {t} ON {main_table}.{col_source} = {t}.{col_target}"
                    joined = True
                    joined_set.add(t)
                    break
            
            if not joined:
                # Reverse FK t -> main
                for fk in schema[t].get("foreign_keys", []):
                    if fk["referred_table"] == main_table:
                        col_source = fk['constrained_columns'][0]
                        col_target = fk['referred_columns'][0]
                        from_clause += f" {join_type} {t} ON {t}.{col_source} = {main_table}.{col_target}"
                        joined = True
                        joined_set.add(t)
                        break
                        
            if not joined:
                from_clause += f" {join_type} {t}"
                joined_set.add(t)

        # --------------------------
        # SELECT
        # --------------------------
        select_parts = []

        if aggregate:
            if aggregate == "COUNT":
                select_parts.append("COUNT(*)")
            else:
                col = columns[0] if columns else "*"
                # Resolve col
                res_col = col
                if col != "*":
                     for t in resolved_tables:
                          if col.lower() in [c.lower() for c in schema[t]['columns']]:
                               res_col = f"{t}.{col}"
                               break
                select_parts.append(f"{aggregate}({res_col})")
        else:
            if not columns:
                select_parts.append(f"{main_table}.*")
            else:
                for col in columns:
                    found = False
                    for t in resolved_tables:
                        if col.lower() in [c.lower() for c in schema[t]['columns']]:
                            select_parts.append(f"{t}.{col}")
                            found = True
                            break
                    if not found:
                        select_parts.append(col) # heuristic

        query = f"SELECT {', '.join(select_parts)} FROM {from_clause}"

        # --------------------------
        # WHERE
        # --------------------------
        if conditions:
            where_clauses = []
            for cond in conditions:
                col = cond["column"]
                op = cond["operator"]
                val = cond["value"]

                resolved_col = None
                for t in resolved_tables:
                    if col.lower() in [c.lower() for c in schema[t]['columns']]:
                        resolved_col = f"{t}.{col}"
                        break

                if not resolved_col:
                    resolved_col = f"{main_table}.{col}"

                if op == "LIKE":
                     where_clauses.append(f"{resolved_col} {op} '{val}'")
                else:
                     where_clauses.append(f"{resolved_col} {op} {val}")

            query += " WHERE " + f" {logic} ".join(where_clauses)

        # --------------------------
        # GROUP BY
        # --------------------------
        if group_by:
            # Resolve group by col
            gb_col = group_by
            for t in resolved_tables:
                if group_by.lower() in [c.lower() for c in schema[t]['columns']]:
                    gb_col = f"{t}.{group_by}"
                    break
            query += f" GROUP BY {gb_col}"

        # --------------------------
        # HAVING
        # --------------------------
        if having:
            h = having[0]
            query += f" HAVING {h['column']} {h['operator']} {h['value']}"

        # --------------------------
        # ORDER BY
        # --------------------------
        if order_col:
            res_order = order_col
            for t in resolved_tables:
                 if order_col.lower() in [c.lower() for c in schema[t]['columns']]:
                     res_order = f"{t}.{order_col}"
                     break
            query += f" ORDER BY {res_order} {order_dir}"

        # --------------------------
        # LIMIT / OFFSET
        # --------------------------
        if db_type == "oracle":
            if offset:
                query += f" OFFSET {offset} ROWS"
            if limit:
                query += f" FETCH NEXT {limit} ROWS ONLY"
        else:
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"

        return query

sql_builder = SQLBuilder()
