import pandas as pd
import sqlite3
import re


def validate_csv(file):
    if file is None:
        return False, "No file provided."
    if hasattr(file, "size") and file.size > 50 * 1024 * 1024:
        return False, "File exceeds the 50MB size limit."
    name = getattr(file, "name", "")
    if not name.lower().endswith(".csv"):
        return False, "Only CSV files are supported."
    return True, ""


def parse_csv(file):
    try:
        df = pd.read_csv(file, encoding="utf-8")
    except UnicodeDecodeError:
        file.seek(0)
        df = pd.read_csv(file, encoding="latin-1")
    return df


def detect_schema(df):
    schema = {}
    for col, dtype in df.dtypes.items():
        dtype_str = str(dtype)
        if dtype_str in ("int64", "int32"):
            schema[col] = "INTEGER"
        elif dtype_str in ("float64", "float32"):
            schema[col] = "REAL"
        elif "datetime64" in dtype_str:
            schema[col] = "DATE"
        else:
            schema[col] = "TEXT"
    return schema


def get_table_name(filename):
    name = filename
    if name.lower().endswith(".csv"):
        name = name[:-4]
    name = name.lower()
    name = re.sub(r"[ \-\.]", "_", name)
    name = re.sub(r"[^\w]", "", name)
    return f"tbl_{name}"


def create_sqlite(df, table_name):
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql(table_name, conn, index=False, if_exists="replace")
    conn.commit()
    return conn


def process_upload(file):
    try:
        is_valid, error_msg = validate_csv(file)
        if not is_valid:
            return None, None, None, None, error_msg

        df = parse_csv(file)
        schema = detect_schema(df)
        table_name = get_table_name(file.name)
        conn = create_sqlite(df, table_name)
        return conn, schema, table_name, df, None
    except Exception as e:
        return None, None, None, None, f"Failed to process file: {str(e)}"


def process_upload_df(df, filename):
    """Accept a pre-loaded DataFrame instead of a file object."""
    try:
        schema = detect_schema(df)
        table_name = get_table_name(filename)
        conn = create_sqlite(df, table_name)
        return conn, schema, table_name, df, None
    except Exception as e:
        return None, None, None, None, f"Failed to process dataset: {str(e)}"
