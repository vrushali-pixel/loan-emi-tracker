"""Loan endpoints: create, list, and fetch a loan with its EMI schedule."""

from __future__ import annotations

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.emi_calculator import calculate_emi_schedule

router = APIRouter(prefix="/loans", tags=["loans"])


def _to_detail(loan: models.Loan) -> schemas.LoanDetailOut:
    schedule = calculate_emi_schedule(
        principal=loan.principal,
        tenure_months=loan.tenure_months,
        annual_rate=loan.annual_rate,
        start_date=loan.start_date,
    )
    return schemas.LoanDetailOut(
        id=loan.id,
        member_id=loan.member_id,
        principal=loan.principal,
        tenure_months=loan.tenure_months,
        annual_rate=loan.annual_rate,
        start_date=loan.start_date,
        created_at=loan.created_at,
        schedule=schedule,
    )


@router.get("", response_model=List[schemas.LoanOut])
def list_loans(db: Session = Depends(get_db)) -> List[models.Loan]:
    return list(db.scalars(select(models.Loan).order_by(models.Loan.id)))


@router.post(
    "", response_model=schemas.LoanDetailOut, status_code=status.HTTP_201_CREATED
)
def create_loan(
    payload: schemas.LoanCreate, db: Session = Depends(get_db)
) -> schemas.LoanDetailOut:
    member = db.get(models.Member, payload.member_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    start_date = payload.start_date or date.today()

    try:
        calculate_emi_schedule(
            principal=payload.principal,
            tenure_months=payload.tenure_months,
            annual_rate=payload.annual_rate,
            start_date=start_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    loan = models.Loan(
        member_id=payload.member_id,
        principal=payload.principal,
        tenure_months=payload.tenure_months,
        annual_rate=payload.annual_rate,
        start_date=start_date,
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)

    return _to_detail(loan)


@router.get("/{loan_id}", response_model=schemas.LoanDetailOut)
def get_loan(loan_id: int, db: Session = Depends(get_db)) -> schemas.LoanDetailOut:
    loan = db.get(models.Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    return _to_detail(loan)