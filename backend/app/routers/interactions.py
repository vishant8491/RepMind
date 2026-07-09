from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import InteractionCreate, InteractionUpdate, InteractionOut

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.get("", response_model=List[InteractionOut])
def list_interactions(hcp_name: Optional[str] = None, db: Session = Depends(get_db)):
    results = crud.list_interactions(db, hcp_name=hcp_name)
    return [InteractionOut(**r.to_dict()) for r in results]


@router.post("", response_model=InteractionOut, status_code=201)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    try:
        interaction = crud.create_interaction(db, payload.model_dump(mode="json"), source="form")
    except crud.ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)
    return InteractionOut(**interaction.to_dict())


@router.get("/{interaction_id}", response_model=InteractionOut)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = crud.get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found.")
    return InteractionOut(**interaction.to_dict())


@router.put("/{interaction_id}", response_model=InteractionOut)
def update_interaction(interaction_id: int, payload: InteractionUpdate, db: Session = Depends(get_db)):
    try:
        data = payload.model_dump(mode="json", exclude_unset=True)
        interaction = crud.update_interaction(db, interaction_id, data)
    except crud.ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found.")
    return InteractionOut(**interaction.to_dict())


@router.delete("/{interaction_id}", status_code=204)
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_interaction(db, interaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Interaction not found.")
    return None
