# HCP CRM — Log Interaction Screen (AI-First)

An AI-first "Log HCP Interaction" screen for a pharma CRM. A sales rep can log a
Healthcare Professional (HCP) interaction either through a **structured form** or
through a **conversational AI Assistant**, backed by a **LangGraph** agent using a
**Groq**-hosted LLM (`gemma2-9b-it`).

## Role of the LangGraph agent

The agent sits between the rep's natural-language input (typed into the "AI
Assistant" chat panel) and the structured `Interaction` records in the database.
Instead of manually filling every form field, the rep can describe what happened
in plain language — e.g. *"Met Dr. Sharma, discussed OncoBoost Phase III data,
she seemed positive, shared the brochure, follow up next week"* — and the agent
decides which tool to call (log a new interaction, edit an existing one, look up
history, summarize a relationship, or suggest next steps), using the LLM both to
route the request and to turn the free text into structured fields inside each
tool. Conversation memory is kept per session (via a LangGraph checkpointer), so
follow-up messages like *"actually make that sentiment negative"* work without
repeating the interaction ID.

## The 5 LangGraph tools

| Tool | Purpose |
|---|---|
| **`log_interaction`** *(mandatory)* | Takes a free-text description of an interaction, uses the LLM to extract structured fields (HCP name, type, topics, materials/samples, sentiment, outcomes, follow-ups), and saves a new record. |
| **`edit_interaction`** *(mandatory)* | Takes an interaction ID and a free-text description of the change, uses the LLM to compute a structured diff, and applies it to the existing record. |
| `search_interactions` | Finds past interactions by HCP name or topic keyword — used by the agent to find an ID before editing, or to answer "what did we discuss with Dr. X last time?". |
| `summarize_hcp_history` | Uses the LLM to produce a short briefing (sentiment trend, recurring topics, open follow-ups) from all past interactions with a given HCP — for a rep prepping for a visit. |
| `suggest_follow_up_actions` | Uses the LLM to propose 2-4 concrete next steps for a specific logged interaction — mirrors the "AI Suggested Follow-ups" panel shown after logging. |

`log_interaction` and `edit_interaction` both use the LLM for summarization/entity
extraction from free text, exactly as required.

## A note on the LLM model

The assignment spec asks for `gemma2-9b-it` on Groq. That model was **permanently
shut down by Groq on October 8, 2025** (deprecated in favor of `llama-3.1-8b-instant`
— see https://console.groq.com/docs/deprecations). It will not appear anywhere in
the Groq console no matter what you try.

The assignment document itself names `llama-3.3-70b-versatile` as an acceptable
alternative ("You may also consider llama-3.3-70b-versatile for context"), and
that model is confirmed active on Groq's current production models list, so it's
used as the default here (`GROQ_MODEL` in `.env.example`). Swap it for any other
currently-active Groq model ID if you'd prefer — nothing else in the code needs
to change.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React 18 + Redux Toolkit, plain CSS, Google Inter font |
| Backend | Python + FastAPI |
| AI agent framework | LangGraph (`create_react_agent` + `MemorySaver` checkpointer) |
| LLM | Groq API, `gemma2-9b-it` |
| Database | MySQL (TiDB Cloud, free tier) via SQLAlchemy + PyMySQL |

## Project structure

```
hcp-crm/
  backend/
    app/
      main.py            # FastAPI app, CORS, table creation
      database.py         # SQLAlchemy engine/session (TLS for hosted MySQL)
      models.py            # Interaction table
      schemas.py            # Pydantic request/response models
      crud.py                # Shared validation + DB helpers (used by API + tools)
      routers/
        interactions.py      # REST CRUD for the structured form
        chat.py                # POST /api/chat -> runs the LangGraph agent
      agent/
        llm.py                  # Groq client factory
        tools.py                  # The 5 LangGraph tools
        graph.py                    # Agent wiring (create_react_agent + prompt)
    requirements.txt
    .env.example
  frontend/
    src/
      components/
        LogInteractionForm.jsx   # Structured form (left panel)
        ChatPanel.jsx              # AI Assistant chat (right panel)
        InteractionHistory.jsx       # List / search / edit / delete table
        TagInput.jsx                   # Reusable tag-list input
      store/                              # Redux Toolkit slices
      api/client.js                        # Axios instance
    .env.example
```

## 1. Setting up the database (TiDB Cloud — same as before)

You can reuse your existing TiDB Cloud account:

1. In the TiDB Cloud console, create a **new Serverless cluster** (or a new database
   inside your existing one) — name it something like `hcp_crm`.
2. Get the connection details (host, user, password) from **Connect**.
3. Build your connection string in this format (note: `mysql+pymysql://`, not
   just `mysql://`, because the backend uses SQLAlchemy + PyMySQL):
   ```
   mysql+pymysql://<user>:<password>@<host>:4000/hcp_crm
   ```
   TLS is handled in code (`app/database.py`, via `certifi`), so you don't need
   any `?ssl=...` query params in the URL itself.

## 2. Getting a free Groq API key

1. Go to https://console.groq.com and sign up (free).
2. Go to **API Keys** → **Create API Key**.
3. Copy the key — you'll only see it once.

## 3. Running the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: paste your DATABASE_URL and GROQ_API_KEY

uvicorn app.main:app --reload --port 8000
```

The `Interaction` table is created automatically on first startup. Visit
http://localhost:8000/docs for interactive API docs (Swagger UI) — useful for
testing the REST endpoints directly.

## 4. Running the frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env    # defaults to http://localhost:8000, change if needed
npm run dev
```

Open http://localhost:5173. You should see the "Log HCP Interaction" screen —
structured form on the left, AI Assistant chat on the right, and an interaction
history table below.

## 5. Trying it out

**Via the form:** fill in the fields and click "Log interaction". AI-suggested
follow-ups appear below the form after saving (this itself calls the
`suggest_follow_up_actions` tool through the agent).

**Via chat**, try messages like:
- *"Met Dr. Sharma today, discussed OncoBoost Phase III efficacy data, she seemed
  positive about it, I shared the brochure and left 2 samples, follow up by
  sending the full PDF."* → calls `log_interaction`
- *"What have we discussed with Dr. Sharma before?"* → calls `search_interactions`
- *"Change the sentiment on that last interaction to Neutral"* → calls
  `edit_interaction` (using `search_interactions` first if needed)
- *"Give me a summary of our history with Dr. Sharma before my next visit."* →
  calls `summarize_hcp_history`

Each assistant reply shows a small badge for any tool it called, so you (and the
demo video viewer) can see exactly which of the 5 tools ran.

## 6. One thing I'd improve with more time

Right now each LangGraph tool opens its own short-lived DB session and makes an
independent LLM call for extraction — simple and reliable for a demo, but it
means `log_interaction` followed immediately by a `suggest_follow_up_actions`
call (as happens after every form save) makes two separate round-trips to Groq.
With more time, I'd add a lightweight in-process cache/queue so the agent can
batch or reuse context across tool calls in the same turn, and move to a
proper connection-pooled async DB session shared across a request instead of
opening a fresh one per tool call.

## 7. Where and how AI was used

Claude was used to scaffold the whole project: the FastAPI backend structure,
the SQLAlchemy models, the LangGraph agent and its 5 tools, the React/Redux
frontend, and this README. All generated code was reviewed and tested end to
end (REST CRUD verified with live requests against a test database; the
LangGraph agent graph verified to compile with all 5 tools wired correctly)
before being handed over. The Groq LLM calls themselves (inside `log_interaction`,
`edit_interaction`, `summarize_hcp_history`, `suggest_follow_up_actions`) require
a live API key to actually run and were not executed as part of this build step —
you'll be exercising those live the first time you use the chat panel. The
`gemma2-9b-it` → `llama-3.3-70b-versatile` model substitution (see above) was
identified by checking Groq's current deprecations page rather than assumed.

## Known minor issue

`npm audit` flags a moderate advisory in `esbuild` (bundled with Vite 5) that
only affects Vite's local dev server accepting cross-origin requests — it does
not affect the production build. Fixing it requires an upstream Vite 8 upgrade,
which is out of scope for this assignment's timeline.
