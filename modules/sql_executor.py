import pandas as pd


def run_query(sql, conn):
    try:
        df = pd.read_sql_query(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)


def format_results(df):
    result = df.copy()
    for col in result.columns:
        if pd.api.types.is_float_dtype(result[col]):
            result[col] = result[col].round(2)
        elif pd.api.types.is_string_dtype(result[col]) or result[col].dtype == object:
            result[col] = result[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
    return result


def get_preview(df, n=2):
    return df.head(n)


def get_remainder(df, n=2):
    return df.iloc[n:]


def extract_stats(df, question):
    stats = []

    # Stat 1: always row count
    stats.append(f"Rows: {len(df)}")

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    if len(numeric_cols) >= 1:
        col = numeric_cols[0]
        val = df[col].max()
        if isinstance(val, float):
            val = round(val, 2)
        stats.append(f"{col}: {val}")
    else:
        stats.append(f"Columns: {len(df.columns)}")

    if len(numeric_cols) >= 2:
        col = numeric_cols[1]
        val = df[col].min()
        if isinstance(val, float):
            val = round(val, 2)
        stats.append(f"{col} min: {val}")
    else:
        stats.append(f"Columns: {len(df.columns)}")

    return stats[:3]
