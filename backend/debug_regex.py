import re

queries = [
    "give the records name,id,salary from departments and employees table where id<=2 and salary>60000",
    "give the first two records with name,id,salary from departments and employees"
]

def test(q):
    print(f"\nQuery: {q}")
    q_norm = q.lower().replace("(", " ( ").replace(")", " ) ").replace(",", " , ")
    # Simple normalization for my debug
    q_norm = q.lower() 
    
    print(f"Norm: {q_norm}")
    
    # LIMIT
    first_match = re.search(r'first\s+(\d+)', q_norm)
    if first_match:
        print("Limit (digits):", first_match.group(1))
        q_norm = re.sub(r'first\s+\d+\s+(records|rows)?', '', q_norm)
    
    word_limit_match = re.search(r'first\s+(one|two|three|four|five|ten)', q_norm)
    if word_limit_match:
         print("Limit (words):", word_limit_match.group(1))
         q_norm = re.sub(r'first\s+(one|two|three|four|five|ten)\s+(records|rows)?(?:\s+with)?', '', q_norm)
         print(f"Post-Limit clean: '{q_norm}'")

    # COLUMNS
    select_match = re.search(r'^(?:give|show|list|select|display)\s+(?:the\s+)?(?:records|details|info)?\s*(.*?)\s+from', q_norm)
    if select_match:
         print("Select Match Group 1:", select_match.group(1))
    else:
         print("No Select Match")

test(queries[0])
test(queries[1])
