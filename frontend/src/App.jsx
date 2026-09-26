import { useState } from 'react';
import { formatINRCurrency } from './utils/formatCurrency';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const INITIAL_FORM = {
  member_id: '',
  principal: '',
  tenure_months: '',
  annual_rate: '8',
  start_date: '',
};

export default function App() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [loan, setLoan] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  function updateField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/loans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          member_id: Number(form.member_id),
          principal: Number(form.principal),
          tenure_months: Number(form.tenure_months),
          annual_rate: Number(form.annual_rate),
          start_date: form.start_date || undefined,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Could not calculate the EMI schedule.');
      }
      setLoan(await res.json());
    } catch (err) {
      setError(err.message);
      setLoan(null);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="mx-auto max-w-3xl space-y-8">
        <h1 className="text-2xl font-semibold text-slate-900">Loan EMI Tracker</h1>

        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4 rounded-xl bg-white p-6 shadow-sm">
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            Member ID
            <input
              type="number"
              required
              value={form.member_id}
              onChange={(e) => updateField('member_id', e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-slate-700">
            Principal (₹)
            <input
              type="number"
              min="1"
              required
              value={form.principal}
              onChange={(e) => updateField('principal', e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-slate-700">
            Tenure (months)
            <input
              type="number"
              min="1"
              required
              value={form.tenure_months}
              onChange={(e) => updateField('tenure_months', e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm text-slate-700">
            Annual rate (%)
            <input
              type="number"
              min="0"
              step="0.1"
              required
              value={form.annual_rate}
              onChange={(e) => updateField('annual_rate', e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </label>

          <label className="col-span-2 flex flex-col gap-1 text-sm text-slate-700">
            Start date (optional)
            <input
              type="date"
              value={form.start_date}
              onChange={(e) => updateField('start_date', e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </label>

          <button
            type="submit"
            disabled={isLoading}
            className="col-span-2 rounded-lg bg-teal-700 py-2 font-medium text-white hover:bg-teal-800 disabled:opacity-50"
          >
            {isLoading ? 'Calculating…' : 'Calculate EMI'}
          </button>
        </form>

        {error && <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}

        {loan && (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl bg-white p-5 shadow-sm">
                <p className="text-sm text-slate-500">Monthly EMI</p>
                <p className="mt-1 text-2xl font-semibold text-slate-900">
                  {formatINRCurrency(loan.monthly_emi)}
                </p>
              </div>
              <div className="rounded-xl bg-white p-5 shadow-sm">
                <p className="text-sm text-slate-500">Total Interest</p>
                <p className="mt-1 text-2xl font-semibold text-slate-900">
                  {formatINRCurrency(loan.total_interest)}
                </p>
              </div>
            </div>

            <div className="overflow-x-auto rounded-xl bg-white shadow-sm">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="px-4 py-3">EMI #</th>
                    <th className="px-4 py-3">Due date</th>
                    <th className="px-4 py-3 text-right">EMI</th>
                    <th className="px-4 py-3 text-right">Principal</th>
                    <th className="px-4 py-3 text-right">Interest</th>
                    <th className="px-4 py-3 text-right">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {loan.schedule.map((row) => (
                    <tr key={row.month} className="border-b border-slate-100 last:border-0">
                      <td className="px-4 py-2">{row.month}</td>
                      <td className="px-4 py-2">{row.due_date ?? '—'}</td>
                      <td className="px-4 py-2 text-right tabular-nums">{formatINRCurrency(row.emi)}</td>
                      <td className="px-4 py-2 text-right tabular-nums">
                        {formatINRCurrency(row.principal_paid)}
                      </td>
                      <td className="px-4 py-2 text-right tabular-nums">
                        {formatINRCurrency(row.interest_paid)}
                      </td>
                      <td className="px-4 py-2 text-right tabular-nums">
                        {formatINRCurrency(row.remaining_balance)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}