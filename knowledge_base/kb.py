KB = [
    {
        "topic": "what is queryMind",
        "content": (
            "QueryMind is an AI-powered data analysis tool that lets you upload CSV files and ask questions "
            "about your data in plain English — no SQL or programming knowledge required. "
            "It automatically converts your natural language questions into SQL queries, runs them against "
            "your data, and delivers both the raw results and an AI-generated analytical summary in seconds."
        ),
    },
    {
        "topic": "how nl to sql works",
        "content": (
            "When you type a question, QueryMind sends that question along with the detected column names "
            "and data types of your uploaded table to Claude AI, which generates a valid SQLite SQL query. "
            "The query is then validated for safety — blocking any destructive operations — before being "
            "executed against your in-memory database, ensuring both accuracy and security."
        ),
    },
    {
        "topic": "how csv upload works",
        "content": (
            "When you upload a CSV file, QueryMind reads it using pandas and automatically detects the "
            "data type of each column (INTEGER, REAL, TEXT, or DATE). It then creates an in-memory SQLite "
            "database for the session so your queries run instantly without any external database setup. "
            "The data is processed entirely within your session and never persisted to disk."
        ),
    },
    {
        "topic": "how the pipeline works",
        "content": (
            "The visual pipeline shows four stages for every query: Parsing (interpreting your question), "
            "SQL Generation (calling Claude AI to write the query), Executing (running the SQL against "
            "your data), and Summarizing (generating an AI-written insight). Each stage animates as it "
            "becomes active, and the generated SQL appears as soon as it is ready so you can inspect it "
            "before the full pipeline completes."
        ),
    },
    {
        "topic": "how the summary works",
        "content": (
            "After your query executes successfully, QueryMind sends up to 40 rows of the result along "
            "with your original question back to Claude AI, which writes a concise one-paragraph analytical "
            "insight. The summary is designed to highlight the most business-relevant finding in plain "
            "English, with specific numbers, rather than just restating what the table contains."
        ),
    },
    {
        "topic": "what kinds of questions work best",
        "content": (
            "Questions asking for totals, averages, top N records, filters by value or date range, "
            "comparisons between groups, and counts of distinct values all work very well. "
            "Highly vague or ambiguous questions may lead to imprecise SQL — the more specific you are "
            "about what you want to see, the better the generated query will be."
        ),
    },
    {
        "topic": "data privacy and security",
        "content": (
            "Your CSV data never leaves your session — it is stored exclusively in an in-memory SQLite "
            "database that is automatically destroyed when your browser session ends. Only the column "
            "schema (names and types) and up to 40 rows of query results are sent to the Claude API "
            "for summarization; your raw data file is never transmitted to any external service."
        ),
    },
    {
        "topic": "how to export results",
        "content": (
            "A download button labeled 'Export CSV' appears below the results table after every successful "
            "query. Clicking it downloads the complete query result — not just the preview rows — as a "
            "CSV file named 'queryMind_results.csv' directly to your device."
        ),
    },
    {
        "topic": "what is the rate limit",
        "content": (
            "Each browser session allows up to 20 queries to prevent excessive API usage. A progress bar "
            "in the sidebar tracks how many queries you have used out of your 20-query allowance. "
            "Refreshing the page starts a new session and resets the counter to zero."
        ),
    },
    {
        "topic": "how the chatbot works",
        "content": (
            "The chatbot in the sidebar is powered by Claude AI and uses a built-in knowledge base about "
            "QueryMind to answer your questions. It retrieves the most relevant knowledge base entries "
            "based on your query and injects them into the AI prompt, so answers are grounded in accurate "
            "information about the tool. The chatbot does not have access to your uploaded data."
        ),
    },
    {
        "topic": "what claude api is",
        "content": (
            "Claude is an AI assistant model created by Anthropic. QueryMind uses Claude's API to power "
            "three features: converting your plain English questions into SQL queries, generating plain "
            "English analytical summaries of query results, and answering your chatbot questions about "
            "how the tool works. All three features use the fast and efficient claude-haiku model."
        ),
    },
    {
        "topic": "error handling",
        "content": (
            "If SQL generation fails or the generated SQL produces a database error, QueryMind displays "
            "a clear, friendly error message on the relevant pipeline stage rather than crashing. "
            "Failed SQL generation attempts do not count against your 20-query rate limit, so you can "
            "rephrase your question and try again without penalty."
        ),
    },
]
