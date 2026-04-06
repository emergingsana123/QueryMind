# QueryMind

A natural language data analysis tool built with Streamlit. Upload any CSV file, ask questions in plain English, and get back SQL queries, live results, and AI-generated insights — no SQL knowledge required.

---

## Overview

QueryMind bridges the gap between raw tabular data and human understanding. Instead of writing SQL by hand, users type questions the way they would ask a colleague. The app translates those questions into valid SQLite queries, executes them against the uploaded data, and produces a concise written analysis of the results.

The entire pipeline — question parsing, SQL generation, query execution, and summarization — is visible in real time through an animated step-by-step progress view.

---

## Features

- **Natural language to SQL** — Type any question about your data in plain English. The app generates a syntactically correct SQLite query using a large language model API.
- **Live pipeline view** — Watch each stage (Parsing, SQL Generation, Executing, Summarizing) animate in real time with timing information.
- **AI-generated analysis** — Every query result is accompanied by a short written summary that interprets the data in plain language.
- **Schema-aware querying** — The app reads your CSV schema and injects real sample rows into the prompt, so the generated SQL uses exact column names and data values from your file.
- **Query history** — Every successful query is saved in the session and can be re-run with one click from the sidebar.
- **Suggestion chips** — On load, the app generates three relevant example questions based on your specific dataset so users know where to start.
- **CSV export** — Download any query result as a CSV file.
- **Built-in sample dataset** — A 50-row sales dataset is included so the app can be tested immediately without uploading a file.
- **Safety filter** — All generated SQL is checked against a blocklist of destructive keywords (DROP, DELETE, INSERT, UPDATE, etc.) before execution.
- **Sidebar chatbot** — A lightweight question-answering assistant answers questions about how the app works, restricted strictly to QueryMind-related topics.
- **Session usage tracking** — A progress bar shows how many queries have been used in the current session against a configurable limit.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| Language model | Anthropic API |
| Data processing | Pandas |
| Query engine | SQLite (in-memory) |
| Styling | Custom CSS with CSS variables |
| Environment | Python 3.10+ |

---

## Project Structure

```
QueryMind/
|-- app.py                      Main application entry point
|-- requirements.txt            Python dependencies
|-- .streamlit/
|   |-- config.toml             Theme and server configuration
|-- modules/
|   |-- csv_handler.py          CSV parsing, schema detection, SQLite loading
|   |-- nl_to_sql.py            Prompt construction and SQL generation via API
|   |-- sql_executor.py         Query execution and result formatting
|   |-- summarizer.py           AI summary generation for query results
|   |-- session.py              Session state initialization and helpers
|   |-- chatbot.py              Sidebar chatbot with topic filtering
|-- data/
|   |-- default_dataset.csv     Built-in 50-row sample sales dataset
|-- knowledge_base/
|   |-- kb.py                   Static knowledge base for the chatbot
|-- styles/
|   |-- main.css                Full custom stylesheet with CSS variables
```

---

## How It Works

### 1. CSV Upload and Schema Detection

When a user uploads a CSV file, `csv_handler.py` reads it with Pandas, infers each column's data type (INTEGER, REAL, DATE, or TEXT), and loads the data into an in-memory SQLite database using `sqlite3.connect(":memory:")`. The schema and database connection are stored in the Streamlit session state.

### 2. SQL Generation

When the user submits a question, `nl_to_sql.py` builds a prompt that includes:
- The table name
- All column names and their types
- Five sample rows from the actual data (so the model uses real values, not invented ones)
- The user's question

This prompt is sent to the language model API. The response is cleaned (markdown stripped, semicolon appended if missing) and checked against the safety blocklist before use.

### 3. Query Execution

`sql_executor.py` runs the cleaned SQL against the in-memory SQLite connection. Results are returned as a Pandas DataFrame. The module also handles type-aware formatting using `pd.api.types` to ensure compatibility with Pandas 2.x string types.

### 4. Summarization

`summarizer.py` sends the query results (as CSV text) along with the original question to the language model API. It requests a concise plain-English interpretation, enforcing a roughly 120-word target. The summary is split into short paragraphs for readability in the UI.

### 5. Rendering

Results are displayed in a top-to-bottom flow:
1. The generated SQL in a dark code block with syntax highlighting
2. The results table (first 5 rows visible by default, expandable)
3. The AI analysis card below, with stat pills summarizing key numbers

---

## Installation

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key

### Setup

```bash
# Clone the repository
git clone https://github.com/emergingsana123/QueryMind.git
cd QueryMind

# Install dependencies
pip install -r requirements.txt

# Create a .env file with your API key
echo ANTHROPIC_API_KEY=your_key_here > .env

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Configuration

### Theme

The visual theme is controlled by `.streamlit/config.toml`:

```toml
[theme]
base = "light"
backgroundColor = "#F8F7FF"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#1E1B4B"
primaryColor = "#6366F1"
font = "sans serif"

[server]
maxUploadSize = 50
```

### Session query limit

The per-session query limit defaults to 20. To change it, update the `rate_limit` value in `modules/session.py`:

```python
def init_session():
    defaults = {
        "rate_limit": 20,   # change this
        ...
    }
```

### File size limit

The maximum CSV upload size is set to 50 MB in `config.toml` via `maxUploadSize = 50`.

---

## Deployment on Streamlit Cloud

1. Push the repository to GitHub (the repo must be public for the free tier).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select the repository, set branch to `main`, and set the main file to `app.py`.
4. Before deploying, open **Advanced settings** and add your API key under **Secrets**:

```toml
ANTHROPIC_API_KEY = "your_key_here"
```

5. Click **Deploy**. Streamlit will install dependencies from `requirements.txt` automatically.

The deployed app reads the secret via `st.secrets["ANTHROPIC_API_KEY"]` and falls back to the environment variable `ANTHROPIC_API_KEY` for local development.

---

## Sample Dataset

The built-in dataset (`data/default_dataset.csv`) contains 50 sales orders with the following columns:

| Column | Type | Description |
|---|---|---|
| order_id | INTEGER | Unique order identifier |
| customer_name | TEXT | Customer full name |
| product_category | TEXT | Category (Electronics, Clothing, etc.) |
| product_name | TEXT | Specific product name |
| quantity | INTEGER | Number of units ordered |
| unit_price | REAL | Price per unit |
| total_amount | REAL | quantity x unit_price |
| order_date | TEXT | Date in YYYY-MM-DD format |
| region | TEXT | Geographic region (North, South, East, West) |
| status | TEXT | Order status (Completed, Pending, Refunded) |

Example questions that work well with this dataset:
- Show total revenue by product category
- Who are the top 5 customers by total amount?
- How many orders were placed in each region?
- What is the average order value for completed orders?

---

## License

MIT License. See `LICENSE` for details.
