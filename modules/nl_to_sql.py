import anthropic
import re


def _get_client(api_key):
    return anthropic.Anthropic(api_key=api_key)


def build_prompt(question, schema, table_name, data_sample=""):
    col_lines = "\n".join(f"  - {col} ({typ})" for col, typ in schema.items())

    sample_section = ""
    if data_sample:
        sample_section = (
            f"\n\nSample rows from the table (use these to learn exact values):\n"
            f"{data_sample}\n"
            f"IMPORTANT: When filtering by text columns (categories, status, names, etc.), "
            f"use only the exact string values that appear in the sample rows above. "
            f"Do not guess or invent values."
        )

    prompt = (
        f"You are an expert SQL generator for SQLite.\n"
        f"The table is named exactly: {table_name}\n"
        f"Columns and their types:\n{col_lines}"
        f"{sample_section}\n\n"
        f"User question: {question}\n\n"
        f"Return ONLY a valid SQLite SQL query. "
        f"No explanation. No markdown. No backticks. No commentary. "
        f"Just the raw SQL ending with a semicolon."
    )
    return prompt


def generate_sql(question, schema, table_name, api_key, data_sample=""):
    client = _get_client(api_key)
    prompt = build_prompt(question, schema, table_name, data_sample)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=(
            "You are an expert SQL generator. Return only valid SQLite SQL. "
            "No markdown. No explanation. Just SQL. "
            "Always use exact column and value names as provided — never guess."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def clean_sql(raw_sql):
    sql = raw_sql.strip()
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)
    sql = re.sub(r"^sql\s*", "", sql, flags=re.IGNORECASE)
    sql = sql.strip()
    if not sql.endswith(";"):
        sql += ";"
    return sql


def is_safe_query(sql):
    blocked = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE",
               "TRUNCATE", "ATTACH", "DETACH"]
    upper = sql.upper()
    for word in blocked:
        pattern = r"\b" + word + r"\b"
        if re.search(pattern, upper):
            return False, word
    return True, ""


def get_sql(question, schema, table_name, api_key, data_sample=""):
    try:
        raw = generate_sql(question, schema, table_name, api_key, data_sample)
        sql = clean_sql(raw)
        safe, blocked_word = is_safe_query(sql)
        if not safe:
            return None, f"Query blocked: contains disallowed keyword '{blocked_word}'."
        return sql, None
    except Exception as e:
        return None, f"SQL generation failed: {str(e)}"
