import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

type Row = Record<string, unknown>;
type ValidationData = {
  meta?: { workbook?: string; valid_responses?: number; brands_compared?: number; brands_mentioned?: number };
  coverage_provider?: Row[];
  coverage_persona?: Row[];
  coverage_intent?: Row[];
  bootstrap?: Row[];
  sensitivity?: Row[];
};

const titleize = (value: string) => value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

function DataTable({ title, rows }: { title: string; rows?: Row[] }) {
  if (!rows?.length) return <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4"><h3 className="font-semibold">{title}</h3><p className="mt-2 text-sm text-slate-500">No rows available in the exported workbook.</p></section>;
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  return <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
    <h3 className="mb-3 font-semibold text-slate-100">{title}</h3>
    <div className="max-h-96 overflow-auto rounded-lg border border-slate-800">
      <table className="min-w-full text-left text-xs">
        <thead className="sticky top-0 bg-slate-800 text-slate-300"><tr>{columns.map((col) => <th key={col} className="px-3 py-2 font-semibold">{titleize(col)}</th>)}</tr></thead>
        <tbody>{rows.map((row, i) => <tr key={i} className="border-t border-slate-800/80 hover:bg-slate-800/40">{columns.map((col) => {
          const value = row[col];
          const display = value == null ? '—' : typeof value === 'number' ? Number(value.toFixed(4)).toString() : String(value);
          return <td key={col} className="max-w-xs px-3 py-2 text-slate-300">{display}</td>;
        })}</tr>)}</tbody>
      </table>
    </div>
  </section>;
}

export const ValidationView: React.FC<{ data: ValidationData }> = ({ data }) => (
  <div className="space-y-6">
    <div>
      <div className="flex items-center gap-2"><ShieldCheck className="h-6 w-6 text-emerald-400"/><h2 className="text-xl font-bold">Validation & Robustness</h2></div>
      <p className="mt-1 text-sm text-slate-400">Validation tables exported from Person 3's workbook. This view complements the existing Explorer and Provider Benchmark rather than duplicating them.</p>
    </div>
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {[['Valid responses', data.meta?.valid_responses ?? 37], ['Brands compared', data.meta?.brands_compared ?? '—'], ['Brands mentioned', data.meta?.brands_mentioned ?? '—']].map(([label, value]) => <div key={String(label)} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4"><p className="text-xs text-slate-400">{label}</p><p className="mt-1 text-2xl font-bold text-white">{value}</p></div>)}
    </div>
    <div className="flex gap-3 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-sm text-amber-200"><AlertTriangle className="h-5 w-5 shrink-0"/><p>Only 37 valid non-comparison responses underpin the headline visibility results. Treat small-slice differences and single-mention flags cautiously.</p></div>
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <DataTable title="Bootstrap ranking" rows={data.bootstrap}/>
      <DataTable title="Sensitivity analysis" rows={data.sensitivity}/>
      <DataTable title="Coverage by provider" rows={data.coverage_provider}/>
      <DataTable title="Coverage by persona" rows={data.coverage_persona}/>
      <DataTable title="Coverage by query type" rows={data.coverage_intent}/>
    </div>
  </div>
);
