"""
The five tools available to the LangGraph agent.

Two are mandatory per the assignment spec:
  - log_interaction   : captures a new interaction (uses the LLM to turn a
                         free-text description into structured fields).
  - edit_interaction  : modifies an already-logged interaction.

The other three round out a realistic sales-rep workflow:
  - search_interactions        : find past interactions for an HCP.
  - summarize_hcp_history      : LLM-generated summary of an HCP's history,
                                  used to brief a rep before a visit.
  - suggest_follow_up_actions  : LLM-generated next-step suggestions for a
                                  specific interaction (mirrors the "AI
                                  Suggested Follow-ups" panel in the mockup).

Each tool opens its own short-lived DB session — simplest approach for an
agent whose tools may run in any order, any number of times, per turn.
"""

import json
from datetime import date as date_type

from langchain_core.tools import tool

from app.database import SessionLocal
from app.crud import (
    ValidationError,
    create_interaction,
    update_interaction,
    get_interaction,
    search_hcp_interactions,
)
from app.agent.llm import get_llm

EXTRACTION_SYSTEM_PROMPT = """You extract structured sales-call notes from a free-text \
description of a meeting between a pharma sales rep and a Healthcare Professional (HCP).

Return ONLY a JSON object (no markdown, no commentary) with these keys:
- hcp_name (string, required — the HCP's name mentioned in the text)
- interaction_type (one of: Meeting, Call, Email, Conference, Other — guess "Meeting" if unclear)
- topics_discussed (string — a concise summary of what was discussed)
- materials_shared (array of strings — any brochures/documents mentioned, else [])
- samples_distributed (array of strings — any drug samples mentioned, else [])
- sentiment (one of: Positive, Neutral, Negative — your best read of the HCP's reaction)
- outcomes (string — key outcomes or agreements, else empty string)
- follow_up_actions (string — any next steps mentioned, else empty string)

If a field cannot be determined from the text, use a sensible empty default \
(empty string or empty array). Never invent an HCP name — if none is mentioned, \
use "Unknown HCP".
"""


def _extract_fields_from_text(raw_text: str) -> dict:
    """Uses the LLM to turn a free-text interaction description into structured fields."""
    llm = get_llm()
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": raw_text},
    ]
    response = llm.invoke(messages)
    content = response.content.strip()
    # Groq models sometimes wrap JSON in ```json fences despite instructions — strip them.
    if content.startswith("```"):
        content = content.strip("`")
        content = content.replace("json\n", "", 1) if content.startswith("json\n") else content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "hcp_name": "Unknown HCP",
            "interaction_type": "Meeting",
            "topics_discussed": raw_text,
            "materials_shared": [],
            "samples_distributed": [],
            "sentiment": "Neutral",
            "outcomes": "",
            "follow_up_actions": "",
        }


@tool
def log_interaction(raw_description: str, hcp_name: str = "") -> str:
    """Log a new HCP interaction from a free-text description of what happened
    (e.g. "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure").
    Uses the LLM to extract structured details (topics, materials, sentiment, outcomes,
    follow-ups) and saves them as a new interaction record. If the HCP's name is already
    known, pass it in `hcp_name` to make sure it's captured correctly even if the LLM
    extraction misses it.
    """
    extracted = _extract_fields_from_text(raw_description)
    if hcp_name:
        extracted["hcp_name"] = hcp_name
    extracted.setdefault("interaction_date", date_type.today().isoformat())

    db = SessionLocal()
    try:
        interaction = create_interaction(db, extracted, source="chat")
        return json.dumps(
            {
                "status": "logged",
                "interaction_id": interaction.id,
                "details": interaction.to_dict(),
            }
        )
    except ValidationError as e:
        return json.dumps({"status": "error", "errors": e.errors})
    finally:
        db.close()


@tool
def edit_interaction(interaction_id: int, changes_description: str) -> str:
    """Edit an already-logged interaction. `interaction_id` is the numeric ID of the
    interaction to change. `changes_description` is a free-text description of what
    should change (e.g. "change sentiment to Positive and add that a follow-up call
    is scheduled for next week"). Use search_interactions first if you don't already
    know the interaction_id.
    """
    db = SessionLocal()
    try:
        existing = get_interaction(db, interaction_id)
        if not existing:
            return json.dumps({"status": "error", "errors": {"interaction_id": "Not found."}})

        llm = get_llm()
        prompt = f"""Here is the current state of a logged HCP interaction:
{json.dumps(existing.to_dict(), indent=2)}

The user wants to make this change: "{changes_description}"

Return ONLY a JSON object containing just the fields that should change, using \
the same field names and formats as above (interaction_type, interaction_date, \
interaction_time, attendees, topics_discussed, materials_shared, \
samples_distributed, sentiment, outcomes, follow_up_actions, hcp_name). \
Do not include fields that aren't changing."""
        response = llm.invoke([{"role": "user", "content": prompt}])
        content = response.content.strip().strip("`")
        if content.startswith("json\n"):
            content = content[5:]
        changes = json.loads(content)

        updated = update_interaction(db, interaction_id, changes)
        return json.dumps({"status": "updated", "interaction_id": updated.id, "details": updated.to_dict()})
    except (ValidationError, json.JSONDecodeError) as e:
        errors = e.errors if isinstance(e, ValidationError) else {"parse": str(e)}
        return json.dumps({"status": "error", "errors": errors})
    finally:
        db.close()


@tool
def search_interactions(query: str) -> str:
    """Search past logged interactions by HCP name or topic keyword. Returns a list
    of matching interactions with their IDs, dates, and summaries. Use this to find
    an interaction_id before calling edit_interaction, or to answer questions like
    "what did we discuss with Dr. Smith last time?".
    """
    db = SessionLocal()
    try:
        results = search_hcp_interactions(db, query)
        return json.dumps({"count": len(results), "interactions": [r.to_dict() for r in results]})
    finally:
        db.close()


@tool
def summarize_hcp_history(hcp_name: str) -> str:
    """Generate a concise briefing summary of all past interactions with a given HCP,
    useful for a rep preparing for an upcoming visit. Summarizes trends in sentiment,
    recurring topics, and any open follow-up items.
    """
    db = SessionLocal()
    try:
        results = search_hcp_interactions(db, hcp_name)
        if not results:
            return json.dumps({"summary": f"No prior interactions found for '{hcp_name}'."})

        history_text = "\n\n".join(
            f"Date: {r.interaction_date}, Type: {r.interaction_type}, "
            f"Sentiment: {r.sentiment}\nTopics: {r.topics_discussed}\n"
            f"Outcomes: {r.outcomes}\nFollow-ups: {r.follow_up_actions}"
            for r in results
        )
        llm = get_llm()
        prompt = (
            f"Summarize this interaction history with HCP '{hcp_name}' for a sales rep "
            f"preparing for their next visit. Highlight sentiment trend, recurring "
            f"topics, and any still-open follow-up items. Keep it to 4-6 sentences.\n\n"
            f"{history_text}"
        )
        response = llm.invoke([{"role": "user", "content": prompt}])
        return json.dumps({"summary": response.content.strip(), "interaction_count": len(results)})
    finally:
        db.close()


@tool
def suggest_follow_up_actions(interaction_id: int) -> str:
    """Generate AI-suggested follow-up actions for a specific logged interaction
    (e.g. scheduling a follow-up meeting, sending requested materials). Mirrors the
    "AI Suggested Follow-ups" panel a rep sees after logging an interaction.
    """
    db = SessionLocal()
    try:
        interaction = get_interaction(db, interaction_id)
        if not interaction:
            return json.dumps({"status": "error", "errors": {"interaction_id": "Not found."}})

        llm = get_llm()
        prompt = f"""Based on this logged HCP interaction, suggest 2-4 concrete follow-up \
actions a pharma sales rep should take next. Return ONLY a JSON array of short strings.

Interaction:
{json.dumps(interaction.to_dict(), indent=2)}"""
        response = llm.invoke([{"role": "user", "content": prompt}])
        content = response.content.strip().strip("`")
        if content.startswith("json\n"):
            content = content[5:]
        try:
            suggestions = json.loads(content)
        except json.JSONDecodeError:
            suggestions = [content]
        return json.dumps({"interaction_id": interaction_id, "suggestions": suggestions})
    finally:
        db.close()


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    search_interactions,
    summarize_hcp_history,
    suggest_follow_up_actions,
]
