from datetime import datetime, date as date_type
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import Interaction
from app.schemas import SENTIMENTS, INTERACTION_TYPES


class ValidationError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


def _parse_date(value) -> date_type:
    if isinstance(value, date_type):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date: {value!r}. Expected YYYY-MM-DD.")


def validate_payload(data: dict, partial: bool = False) -> dict:
    """
    Server-side validation shared by the REST API and the LangGraph tools.
    `partial=True` (used for edits) only validates fields that are present.
    """
    errors = {}
    clean = {}

    def has(field):
        return field in data and data[field] is not None

    if not partial or has("hcp_name"):
        name = (data.get("hcp_name") or "").strip()
        if not name:
            errors["hcp_name"] = "HCP name is required."
        else:
            clean["hcp_name"] = name

    if not partial or has("interaction_type"):
        itype = data.get("interaction_type") or "Meeting"
        if itype not in INTERACTION_TYPES:
            errors["interaction_type"] = f"Must be one of: {', '.join(INTERACTION_TYPES)}."
        else:
            clean["interaction_type"] = itype

    if not partial or has("interaction_date"):
        try:
            clean["interaction_date"] = _parse_date(data.get("interaction_date"))
        except ValueError as e:
            errors["interaction_date"] = str(e)

    if has("interaction_time"):
        clean["interaction_time"] = data.get("interaction_time")

    if has("attendees"):
        clean["attendees"] = list(data.get("attendees") or [])

    if has("topics_discussed"):
        clean["topics_discussed"] = data.get("topics_discussed")

    if has("materials_shared"):
        clean["materials_shared"] = list(data.get("materials_shared") or [])

    if has("samples_distributed"):
        clean["samples_distributed"] = list(data.get("samples_distributed") or [])

    if not partial or has("sentiment"):
        sentiment = data.get("sentiment") or "Neutral"
        if sentiment not in SENTIMENTS:
            errors["sentiment"] = f"Must be one of: {', '.join(SENTIMENTS)}."
        else:
            clean["sentiment"] = sentiment

    if has("outcomes"):
        clean["outcomes"] = data.get("outcomes")

    if has("follow_up_actions"):
        clean["follow_up_actions"] = data.get("follow_up_actions")

    if errors:
        raise ValidationError(errors)
    return clean


def create_interaction(db: Session, data: dict, source: str = "form") -> Interaction:
    clean = validate_payload(data, partial=False)
    interaction = Interaction(**clean, source=source)
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def update_interaction(db: Session, interaction_id: int, data: dict) -> Optional[Interaction]:
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        return None
    clean = validate_payload(data, partial=True)
    for key, value in clean.items():
        setattr(interaction, key, value)
    db.commit()
    db.refresh(interaction)
    return interaction


def get_interaction(db: Session, interaction_id: int) -> Optional[Interaction]:
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()


def list_interactions(db: Session, hcp_name: Optional[str] = None, limit: int = 100):
    query = db.query(Interaction)
    if hcp_name:
        query = query.filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
    return query.order_by(Interaction.interaction_date.desc(), Interaction.id.desc()).limit(limit).all()


def delete_interaction(db: Session, interaction_id: int) -> bool:
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        return False
    db.delete(interaction)
    db.commit()
    return True


def search_hcp_interactions(db: Session, name_query: str, limit: int = 20):
    return (
        db.query(Interaction)
        .filter(
            or_(
                Interaction.hcp_name.ilike(f"%{name_query}%"),
                Interaction.topics_discussed.ilike(f"%{name_query}%"),
            )
        )
        .order_by(Interaction.interaction_date.desc())
        .limit(limit)
        .all()
    )
