"""EMI (Equated Monthly Installment) calculator utilities.

Formula:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

where:
    P = principal
    r = monthly interest rate (annual_rate / 100 / 12)
    n = tenure in months
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import List, Optional


def _add_months(start: date, months: int) -> date:
    """Return the date `months` after `start`.

    Clamps the day to the target month's length (e.g. Jan 31 + 1 month
    lands on Feb 28/29 rather than overflowing into March).
    """
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)


def calculate_emi_schedule(
    principal: float,
    tenure_months: int,
    annual_rate: float = 8.0,
    start_date: Optional[date] = None,
) -> List[dict]:
    """Compute a month-by-month EMI amortization schedule.

    Args:
        principal: Loan principal amount. Must be > 0.
        tenure_months: Number of monthly installments. Must be a positive
            integer.
        annual_rate: Nominal annual interest rate in percent (e.g. 8.0
            means 8% per annum). Defaults to 8.0.
        start_date: Optional disbursement date. When provided, each
            schedule entry includes the due date for that installment
            (one calendar month after the previous due date).

    Returns:
        A list of dicts, one per month, in order, each with keys:
            - "month": 1-based installment number
            - "due_date": date or None (present only if start_date given)
            - "emi": EMI amount for that month, rounded to 2 decimals
            - "interest_paid": interest component, rounded to 2 decimals
            - "principal_paid": principal component, rounded to 2 decimals
            - "remaining_balance": principal left after this installment,
              rounded to 2 decimals

        The final entry's "remaining_balance" is guaranteed to be exactly 0.0 —
        the last month's principal component is forced to absorb any
        rounding residue so the loan always closes out cleanly.

    Raises:
        ValueError: if principal <= 0, tenure_months <= 0, or
            annual_rate < 0.
    """
    if principal <= 0:
        raise ValueError("principal must be greater than 0")
    if tenure_months <= 0:
        raise ValueError("tenure_months must be a positive integer")
    if annual_rate < 0:
        raise ValueError("annual_rate must be non-negative")

    r = annual_rate / 100 / 12  # monthly interest rate

    if r == 0:
        emi = principal / tenure_months
    else:
        factor = (1 + r) ** tenure_months
        emi = principal * r * factor / (factor - 1)

    schedule: List[dict] = []
    balance = principal
    due_date = start_date

    for month in range(1, tenure_months + 1):
        is_last = month == tenure_months
        interest_paid = round(balance * r, 2)

        if is_last:
            # Force the final principal component to clear the remaining
            # balance exactly, so the closing balance is strictly 0,
            # absorbing any rounding residue accumulated over the schedule.
            principal_paid = round(balance, 2)
            emi_amount = round(principal_paid + interest_paid, 2)
        else:
            emi_amount = round(emi, 2)
            principal_paid = round(emi_amount - interest_paid, 2)

        balance = 0.0 if is_last else round(balance - principal_paid, 2)

        if start_date is not None:
            due_date = _add_months(start_date, month)

        schedule.append(
            {
                "month": month,
                "due_date": due_date,
                "emi": emi_amount,
                "interest_paid": interest_paid,
                "principal_paid": principal_paid,
                "remaining_balance": balance,
            }
        )

    return schedule