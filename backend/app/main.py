from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import interactions, chat

# Creates the `interactions` table on startup if it doesn't already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HCP CRM — Log Interaction API",
    description="Backend for the AI-first CRM HCP module: structured CRUD "
    "plus a LangGraph agent for conversational interaction logging.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "hcp-crm-backend"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}
