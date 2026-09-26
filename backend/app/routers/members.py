"""Member endpoints: create and list members."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=List[schemas.MemberOut])
def list_members(db: Session = Depends(get_db)) -> List[models.Member]:
    return list(db.scalars(select(models.Member).order_by(models.Member.id)))


@router.post(
    "", response_model=schemas.MemberOut, status_code=status.HTTP_201_CREATED
)
def create_member(
    payload: schemas.MemberCreate, db: Session = Depends(get_db)
) -> models.Member:
    existing = db.scalar(
        select(models.Member).where(models.Member.email == payload.email)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A member with this email already exists",
        )

    member = models.Member(name=payload.name, email=payload.email, phone=payload.phone)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member