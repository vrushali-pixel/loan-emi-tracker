from datetime import date

import pytest

from app.emi_calculator import calculate_emi_schedule


class TestStandardTwelveMonthLoan:
    def setup_method(self):
        self.principal = 120000.0
        self.tenure = 12
        self.annual_rate = 8.0
        self.schedule = calculate_emi_schedule(
            self.principal, self.tenure, self.annual_rate
        )

    def test_schedule_length(self):
        assert len(self.schedule) == self.tenure

    def test_month_numbers_are_sequential(self):
        assert [row["month"] for row in self.schedule] == list(range(1, 13))

    def test_emi_amount_is_stable_across_months(self):
        # All but the last month should charge (about) the same EMI.
        emis = [row["emi"] for row in self.schedule[:-1]]
        assert max(emis) - min(emis) <= 0.01

    def test_balances_are_non_increasing(self):
        balances = [row["balance"] for row in self.schedule]
        assert all(
            balances[i] >= balances[i + 1] for i in range(len(balances) - 1)
        )

    def test_closing_balance_is_exactly_zero(self):
        assert self.schedule[-1]["balance"] == 0.0

    def test_principal_components_sum_to_original_principal(self):
        total_principal = round(
            sum(row["principal"] for row in self.schedule), 2
        )
        assert total_principal == pytest.approx(self.principal, abs=0.01)

    def test_emi_matches_standard_formula(self):
        r = self.annual_rate / 100 / 12
        factor = (1 + r) ** self.tenure
        expected_emi = round(
            self.principal * r * factor / (factor - 1), 2
        )
        # First month's EMI should match the closed-form formula.
        assert self.schedule[0]["emi"] == expected_emi

    def test_due_dates_advance_monthly_when_start_date_given(self):
        start = date(2026, 1, 15)
        schedule = calculate_emi_schedule(
            self.principal, self.tenure, self.annual_rate, start_date=start
        )
        due_dates = [row["due_date"] for row in schedule]
        assert due_dates[0] == date(2026, 2, 15)
        assert due_dates[-1] == date(2027, 1, 15)
        assert due_dates == sorted(due_dates)

    def test_due_date_is_none_without_start_date(self):
        assert all(row["due_date"] is None for row in self.schedule)


class TestOneMonthEdgeCase:
    def test_single_installment_clears_full_balance(self):
        principal = 5000.0
        annual_rate = 8.0
        schedule = calculate_emi_schedule(principal, 1, annual_rate)

        assert len(schedule) == 1
        row = schedule[0]

        r = annual_rate / 100 / 12
        expected_interest = round(principal * r, 2)
        expected_principal = round(principal, 2)
        expected_emi = round(expected_principal + expected_interest, 2)

        assert row["interest"] == expected_interest
        assert row["principal"] == expected_principal
        assert row["emi"] == expected_emi
        assert row["balance"] == 0.0

    def test_single_installment_with_zero_rate(self):
        principal = 1000.0
        schedule = calculate_emi_schedule(principal, 1, annual_rate=0.0)
        row = schedule[0]

        assert row["interest"] == 0.0
        assert row["principal"] == principal
        assert row["emi"] == principal
        assert row["balance"] == 0.0


class TestValidation:
    def test_zero_tenure_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_emi_schedule(100000.0, 0)

    def test_negative_tenure_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_emi_schedule(100000.0, -3)

    def test_zero_principal_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_emi_schedule(0, 12)

    def test_negative_principal_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_emi_schedule(-5000.0, 12)

    def test_negative_rate_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_emi_schedule(100000.0, 12, annual_rate=-1.0)