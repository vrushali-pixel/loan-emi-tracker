"""Reporting endpoints."""

from __future__ import annotations

import csv
import io
from datetime import date
from typing import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.emi_calculator import calculate_emi_schedule

router = APIRouter(prefix="/reports", tags=["reports"])


def _outstanding_balance(loan: models.Loan, as_of: date) -> float:
    """Outstanding principal on `loan` as of `as_of`, derived from its EMI
    schedule (counts installments whose due date has passed)."""
    schedule = calculate_emi_schedule(
        principal=loan.principal,
        tenure_months=loan.tenure_months,
        annual_rate=loan.annual_rate,
        start_date=loan.start_date,
    )
    elapsed = sum(1 for row in schedule if row["due_date"] and row["due_date"] <= as_of)
    if elapsed <= 0:
        return round(loan.principal, 2)
    if elapsed >= len(schedule):
        return 0.0
    return schedule[elapsed - 1]["balance"]


def _generate_csv_rows(db: Session) -> Iterator[str]:
    as_of = date.today()
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    def _flush() -> str:
        value = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        return value

    writer.writerow(
        [
            "member_id",
            "member_name",
            "member_email",
            "total_principal",
            "outstanding_balance",
        ]
    )
    yield _flush()

    members = db.scalars(select(models.Member).order_by(models.Member.id))
    for member in members:
        total_principal = round(sum(loan.principal for loan in member.loans), 2)
        outstanding = round(
            sum(_outstanding_balance(loan, as_of) for loan in member.loans), 2
        )
        writer.writerow(
            [member.id, member.name, member.email, total_principal, outstanding]
        )
        yield _flush()


@router.get("/member-outstanding/csv")
def member_outstanding_csv(db: Session = Depends(get_db)) -> StreamingResponse:
    return StreamingResponse(
        _generate_csv_rows(db),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=member-outstanding.csv"
        },
    )