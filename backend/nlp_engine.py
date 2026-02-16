import spacy
import re
from typing import List, Dict, Any, Tuple

# Load the pretrained model
# In a real app, load this once at startup
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class NLPEngine:
    def __init__(self):
        self.intent_keywords = {
            "SUM": ["total", "sum", "add"],
            "COUNT": ["count", "number of", "how many"],
            "AVG": ["average", "avg", "mean"],
            "MAX": ["highest", "max", "maximum", "top"],
            "MIN": ["lowest", "min", "minimum", "bottom"],
            "GROUP_BY": ["by", "each", "per", "department wise", "category wise"]
        }

    def analyze_query(self, query: str) -> Dict[str, Any]:

        q = query.lower()

        analysis = {
            "tables": [],
            "columns": [],
            "conditions": [],
            "logic": "AND",
            "aggregate": None,
            "group_by": None,
            "having": [],
            "order_by_col": None,
            "order_dir": "ASC",
            "limit": None,
            "offset": None,
            "join_type": "JOIN"
        }

        # --------------------------
        # JOIN TYPE
        # --------------------------
        if "left join" in q:
            analysis["join_type"] = "LEFT JOIN"
        elif "right join" in q:
            analysis["join_type"] = "RIGHT JOIN"
        elif "full join" in q:
            analysis["join_type"] = "FULL JOIN"
        elif "cross join" in q:
            analysis["join_type"] = "CROSS JOIN"

        # --------------------------
        # LIMIT (first N records)
        # --------------------------
        first_match = re.search(r'first\s+(\d+)', q)
        if first_match:
            analysis["limit"] = int(first_match.group(1))
            q = re.sub(r'first\s+\d+\s+(records|rows)?', '', q)
        
        # Word-based limits "first two"
        word_limit_match = re.search(r'first\s+(one|two|three|four|five|ten)', q)
        if word_limit_match:
             w = word_limit_match.group(1)
             mapping = {"one":1, "two":2, "three":3, "four":4, "five":5, "ten":10}
             analysis["limit"] = mapping[w]
             q = re.sub(r'first\s+(one|two|three|four|five|ten)\s+(records|rows)?(?:\s+with)?', '', q)

        # --------------------------
        # OFFSET
        # --------------------------
        offset_match = re.search(r'(?:skip|offset)\s+(\d+)', q)
        if offset_match:
            analysis["offset"] = int(offset_match.group(1))

        # --------------------------
        # ORDER BY
        # --------------------------
        if "highest" in q:
            analysis["order_dir"] = "DESC"
        if "lowest" in q:
            analysis["order_dir"] = "ASC"

        # Explicit "order by col"
        order_match = re.search(r'order by\s+(\w+)', q)
        if order_match:
            analysis["order_by_col"] = order_match.group(1)
        else:
            # Implicit "salary by highest", "age by lowest"
            # Pattern: (word) by (highest|lowest|max|min)
            implicit_order = re.search(r'(\w+)\s+by\s+(?:highest|lowest|max|min|desc|asc)', q)
            if implicit_order:
                analysis["order_by_col"] = implicit_order.group(1)
                # Remove from q to clean up for table extraction
                q = re.sub(r'\w+\s+by\s+(?:highest|lowest|max|min|desc|asc)', '', q)

        # --------------------------
        # AGGREGATION
        # --------------------------
        if "count" in q:
            analysis["aggregate"] = "COUNT"
        elif "sum" in q or "total" in q:
            analysis["aggregate"] = "SUM"
        elif "average" in q:
            analysis["aggregate"] = "AVG"
        elif "max" in q:
            analysis["aggregate"] = "MAX"
        elif "min" in q:
            analysis["aggregate"] = "MIN"

        # --------------------------
        # TABLES
        # --------------------------
        # "from table1, table2" or "from table1 and table2"
        from_match = re.search(r'from\s+(.*?)(?:\s+where|\s+group|\s+order|\s+limit|$)', q)
        if from_match:
            t_part = from_match.group(1)
            parts = re.split(r',|and', t_part)
            analysis["tables"] = [p.strip().replace("table","").strip() for p in parts if p.strip()]

        # Fallback: Detect if logic didn't catch tables but nouns exist? 
        # For now, strict "from" is safer as requested.
        
        # --------------------------
        # COLUMNS
        # --------------------------
        col_match = re.search(r'\((.*?)\)', query) # Use raw for brackets
        if col_match:
            cols = col_match.group(1)
            analysis["columns"] = [c.strip() for c in cols.split(",")]
        else:
            # Enhanced regex to capture columns while ignoring "the records"
            select_match = re.search(r'(?:give|show|list|select)\s+(?:the\s+)?(?:records|details|list|info|rows)?\s*(.*?)\s+from', q)
            if select_match:
                col_part = select_match.group(1)
                # Split by comma or 'and'
                parts = re.split(r',|and', col_part)
                # Filter stopwords and empty strings
                analysis["columns"] = []
                for p in parts:
                    clean_p = p.strip()
                    # Remove "with" if somehow left
                    if clean_p.startswith("with "):
                        clean_p = clean_p[5:].strip()
                    
                    if clean_p and clean_p not in ["records", "the", "details", "all", "list", "info"]:
                        analysis["columns"].append(clean_p)

        # --------------------------
        # WHERE CONDITIONS
        # --------------------------
        where_match = re.search(r'where\s+(.*)', q)
        if where_match:
            where_part = where_match.group(1)

            if " or " in where_part:
                analysis["logic"] = "OR"

            # Improved Regex for <=, >=, !=
            condition_pattern = r'(\w+)\s*(>=|<=|!=|>|<|=|is)\s*(\d+)'
            matches = re.findall(condition_pattern, where_part)

            for col, op, val in matches:
                if op == "is": op = "="
                analysis["conditions"].append({
                    "column": col,
                    "operator": op,
                    "value": val
                })

        # --------------------------
        # GROUP BY
        # --------------------------
        group_match = re.search(r'group by\s+(\w+)', q)
        if group_match:
            analysis["group_by"] = group_match.group(1)

        # --------------------------
        # HAVING
        # --------------------------
        having_match = re.search(r'having\s+(\w+)\s*(>=|<=|>|<|=)\s*(\d+)', q)
        if having_match:
            analysis["having"].append({
                "column": having_match.group(1),
                "operator": having_match.group(2),
                "value": having_match.group(3)
            })

        return analysis

nlp_engine = NLPEngine()
