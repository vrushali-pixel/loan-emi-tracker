"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, computed_field


class MemberCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: Optional[str] = None
    created_at: datetime


class LoanCreate(BaseModel):
    member_id: int
    principal: float
    tenure_months: int
    annual_rate: float = 8.0
    start_date: Optional[date] = None


class EmiScheduleRow(BaseModel):
    month: int
    due_date: Optional[date] = None
    emi: float
    principal_paid: float
    interest_paid: float
    remaining_balance: float


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    principal: float
    tenure_months: int
    annual_rate: float
    start_date: date
    created_at: datetime


class LoanDetailOut(LoanOut):
    schedule: List[EmiScheduleRow]

    @computed_field  # type: ignore[misc]
    @property
    def monthly_emi(self) -> float:
        """EMI charged each month (same for every month except possibly the last)."""
        return self.schedule[0].emi if self.schedule else 0.0

    @computed_field  # type: ignore[misc]
    @property
    def total_interest(self) -> float:
        return round(sum(row.interest_paid for row in self.schedule), 2)