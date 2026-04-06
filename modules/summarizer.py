import anthropic


def _get_client(api_key):
    return anthropic.Anthropic(api_key=api_key)


def truncate_for_prompt(df, max_rows=40):
    if len(df) > max_rows:
        return df.head(max_rows)
    return df


def build_summary_prompt(df, question):
    truncated = truncate_for_prompt(df)
    # Convert StringDtype columns to plain object so CSV is clean
    for col in truncated.select_dtypes(include="string").columns:
        truncated = truncated.copy()
        truncated[col] = truncated[col].astype(object)
    csv_data = truncated.to_csv(index=False)
    prompt = (
        f"You are a data analyst. The user asked: \"{question}\"\n\n"
        f"Here is the query result data:\n{csv_data}\n\n"
        f"Write exactly one paragraph of no more than 120 words. "
        f"Be highly specific with numbers from the data. "
        f"Structure it as: one sentence stating the main finding, "
        f"two to three sentences with specific supporting numbers, "
        f"one sentence with a key takeaway or recommendation. "
        f"Do not use bullet points. Do not use headers. "
        f"Do not start with 'The data shows' or 'Based on the data'. "
        f"Write like a sharp analyst giving a quick briefing."
    )
    return prompt


def _shorten(summary, api_key):
    client = _get_client(api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system="You are a concise editor. Shorten text while keeping all key numbers.",
        messages=[{
            "role": "user",
            "content": f"Shorten this to under 120 words while keeping all key numbers: {summary}",
        }],
    )
    return response.content[0].text.strip()


def generate_summary(df, question, api_key):
    if df is None or len(df) == 0:
        return "No data to analyze — the query returned 0 rows."
    try:
        client = _get_client(api_key)
        prompt = build_summary_prompt(df, question)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system="You are a concise data analyst. Write a single analytical paragraph under 120 words.",
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.content[0].text.strip()

        if len(summary.split()) > 130:
            summary = _shorten(summary, api_key)

        return summary
    except Exception:
        return "Analysis unavailable."
