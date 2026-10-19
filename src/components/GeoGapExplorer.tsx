import React, { useState, useMemo } from 'react';
import { 
  Search, 
  ArrowUpDown, 
  AlertCircle, 
  CheckCircle2, 
  HelpCircle, 
  EyeOff, 
  Info,
  TrendingUp,
  Sparkles,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Target
} from 'lucide-react';
import { BrandGapItem } from '../types';

interface GeoGapExplorerProps {
  data: BrandGapItem[];
}

export const GeoGapExplorer: React.FC<GeoGapExplorerProps> = ({ data }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLabel, setSelectedLabel] = useState<string>('all');
  const [sortField, setSortField] = useState<keyof BrandGapItem>('gap');
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const [selectedBrand, setSelectedBrand] = useState<BrandGapItem | null>(null);

  // Summary counts
  const stats = useMemo(() => {
    const total = data.length;
    const mentioned = data.filter((d) => d.mentions > 0).length;
    const under = data.filter((d) => d.label === 'under-visible').length;
    const over = data.filter((d) => d.label === 'over-visible').length;
    const invisible = data.filter((d) => d.label === 'invisible').length;
    const aligned = data.filter((d) => d.label === 'aligned').length;
    const lowEvidence = data.filter((d) => d.label === 'low-evidence').length;

    return { total, mentioned, under, over, invisible, aligned, lowEvidence };
  }, [data]);

  // Filtering & Sorting
  const filteredData = useMemo(() => {
    return data
      .filter((item) => {
        const matchesSearch = item.brand.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesLabel = selectedLabel === 'all' || item.label === selectedLabel;
        return matchesSearch && matchesLabel;
      })
      .sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];

        // Handle null values in sort
        if (valA === null || valA === undefined) valA = -999999;
        if (valB === null || valB === undefined) valB = -999999;

        if (typeof valA === 'string' && typeof valB === 'string') {
          return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }
        return sortAsc ? (valA as number) - (valB as number) : (valB as number) - (valA as number);
      });
  }, [data, searchTerm, selectedLabel, sortField, sortAsc]);

  const handleSort = (field: keyof BrandGapItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const getLabelBadge = (label: string) => {
    switch (label) {
      case 'under-visible':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            <TrendingUp className="w-3 h-3" /> Under-Visible
          </span>
        );
      case 'over-visible':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
            <AlertCircle className="w-3 h-3" /> Over-Visible
          </span>
        );
      case 'invisible':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
            <EyeOff className="w-3 h-3" /> Invisible
          </span>
        );
      case 'aligned':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-300 border border-blue-500/30">
            <CheckCircle2 className="w-3 h-3" /> Aligned
          </span>
        );
      case 'low-evidence':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/15 text-slate-300 border border-slate-600/30">
            <HelpCircle className="w-3 h-3" /> Low Evidence
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Metric Cards Banner */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl relative overflow-hidden">
          <div className="text-xs text-slate-400 font-medium">Evaluation Cohort</div>
          <div className="text-2xl font-bold text-white mt-1">{stats.total}</div>
          <div className="text-[11px] text-slate-500 mt-1">Top buyers + mentioned</div>
          <div className="absolute right-2 -bottom-2 opacity-10">
            <Target className="w-16 h-16 text-indigo-400" />
          </div>
        </div>

        <div 
          onClick={() => setSelectedLabel(selectedLabel === 'under-visible' ? 'all' : 'under-visible')}
          className={`cursor-pointer transition-all bg-slate-900/80 border p-4 rounded-xl relative overflow-hidden ${
            selectedLabel === 'under-visible' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-800 hover:border-emerald-500/50'
          }`}
        >
          <div className="text-xs text-emerald-400 font-medium flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" /> Under-Visible
          </div>
          <div className="text-2xl font-bold text-emerald-300 mt-1">{stats.under}</div>
          <div className="text-[11px] text-slate-400 mt-1">High merit, LLM penalty</div>
        </div>

        <div 
          onClick={() => setSelectedLabel(selectedLabel === 'over-visible' ? 'all' : 'over-visible')}
          className={`cursor-pointer transition-all bg-slate-900/80 border p-4 rounded-xl relative overflow-hidden ${
            selectedLabel === 'over-visible' ? 'border-rose-500 ring-1 ring-rose-500' : 'border-slate-800 hover:border-rose-500/50'
          }`}
        >
          <div className="text-xs text-rose-400 font-medium flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5" /> Over-Visible
          </div>
          <div className="text-2xl font-bold text-rose-300 mt-1">{stats.over}</div>
          <div className="text-[11px] text-slate-400 mt-1">AI engine bias favor</div>
        </div>

        <div 
          onClick={() => setSelectedLabel(selectedLabel === 'invisible' ? 'all' : 'invisible')}
          className={`cursor-pointer transition-all bg-slate-900/80 border p-4 rounded-xl relative overflow-hidden ${
            selectedLabel === 'invisible' ? 'border-amber-500 ring-1 ring-amber-500' : 'border-slate-800 hover:border-amber-500/50'
          }`}
        >
          <div className="text-xs text-amber-400 font-medium flex items-center gap-1">
            <EyeOff className="w-3.5 h-3.5" /> Invisible
          </div>
          <div className="text-2xl font-bold text-amber-300 mt-1">{stats.invisible}</div>
          <div className="text-[11px] text-slate-400 mt-1">0 mentions in prompts</div>
        </div>

        <div 
          onClick={() => setSelectedLabel(selectedLabel === 'aligned' ? 'all' : 'aligned')}
          className={`cursor-pointer transition-all bg-slate-900/80 border p-4 rounded-xl relative overflow-hidden ${
            selectedLabel === 'aligned' ? 'border-blue-500 ring-1 ring-blue-500' : 'border-slate-800 hover:border-blue-500/50'
          }`}
        >
          <div className="text-xs text-blue-400 font-medium flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Aligned
          </div>
          <div className="text-2xl font-bold text-blue-300 mt-1">{stats.aligned}</div>
          <div className="text-[11px] text-slate-400 mt-1">Fair representation</div>
        </div>

        <div 
          onClick={() => setSelectedLabel(selectedLabel === 'low-evidence' ? 'all' : 'low-evidence')}
          className={`cursor-pointer transition-all bg-slate-900/80 border p-4 rounded-xl relative overflow-hidden ${
            selectedLabel === 'low-evidence' ? 'border-slate-500 ring-1 ring-slate-500' : 'border-slate-800 hover:border-slate-500/50'
          }`}
        >
          <div className="text-xs text-slate-400 font-medium flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5" /> Low Evidence
          </div>
          <div className="text-2xl font-bold text-slate-300 mt-1">{stats.lowEvidence}</div>
          <div className="text-[11px] text-slate-500 mt-1">&lt; 1,000 Amazon reviews</div>
        </div>
      </div>

      {/* 2D Interactive Scatter / Quadrant Visualizer */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-indigo-400" />
              Geo-Gap Quadrant Matrix: Consumer Merit vs AI Engine Visibility
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Plotting Ground-Truth Merit Percentile against Generative Engine Visibility Index. Click any dot to inspect brand diagnostics.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span> Under-Visible
            </span>
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block"></span> Over-Visible
            </span>
            <span className="flex items-center gap-1.5 text-blue-400">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span> Aligned
            </span>
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span> Invisible
            </span>
            <span className="flex items-center gap-1.5 text-slate-400">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block"></span>
              Low-Evidence
            </span>
          </div>
        </div>

        {/* Visual Canvas Representation */}
        <div className="relative h-72 sm:h-80 w-full bg-slate-950/80 border border-slate-800/80 rounded-xl overflow-hidden p-4">
          {/* Quadrant background quadrants & labels */}
          <div className="absolute inset-0 grid grid-cols-2 grid-rows-2 opacity-30 pointer-events-none">
            <div className="border-r border-b border-indigo-500/20 bg-emerald-950/10 p-3">
              <span className="text-[11px] font-medium text-emerald-400 uppercase tracking-wider">
                Top Left: Under-Visible (Deserves More Visibility)
              </span>
            </div>
            <div className="border-b border-indigo-500/20 bg-blue-950/10 p-3 text-right">
              <span className="text-[11px] font-medium text-blue-400 uppercase tracking-wider">
                Top Right: Aligned Leaders
              </span>
            </div>
            <div className="border-r border-indigo-500/20 bg-slate-950/20 p-3 flex items-end">
              <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                Bottom Left: Invisible / Niche
              </span>
            </div>
            <div className="bg-rose-950/10 p-3 flex items-end justify-end">
              <span className="text-[11px] font-medium text-rose-400 uppercase tracking-wider">
                Bottom Right: Over-Visible (AI Darling Bias)
              </span>
            </div>
          </div>

          {/* Neutral center reference axes */}
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-800 border-l border-dashed border-slate-700 pointer-events-none" />
          <div className="absolute top-1/2 left-0 right-0 h-px bg-slate-800 border-t border-dashed border-slate-700 pointer-events-none" />

          {/* Axis Labels */}
          <div className="absolute bottom-1 right-3 text-[10px] font-semibold text-slate-400 tracking-wider">
            AI VISIBILITY INDEX →
          </div>
          <div className="absolute top-2 left-2 text-[10px] font-semibold text-slate-400 tracking-wider">
            ↑ GROUND-TRUTH MERIT %
          </div>

          
{/* Scatter dots: plot every valid brand, not just the first 160 */}
<div className="absolute inset-6">
  {data
    .filter(
      (b) =>
        Number.isFinite(Number(b.merit_pct)) &&
        Number.isFinite(Number(b.visibility_index))
    )
    .map((b) => {
      const merit = Math.min(
        100,
        Math.max(0, Number(b.merit_pct))
      );

      const visibility = Math.min(
        100,
        Math.max(0, Number(b.visibility_index))
      );

      const dotColors: Record<string, string> = {
        'under-visible':
          'bg-emerald-400 ring-2 ring-emerald-500/30',
        'over-visible':
          'bg-rose-500 ring-2 ring-rose-500/30',
        aligned:
          'bg-blue-400 ring-2 ring-blue-500/30',
        invisible:
          'bg-amber-400/80',
        'low-evidence':
          'bg-slate-400 ring-1 ring-slate-300/30',
      };

      const isSelected = selectedBrand?.brand === b.brand;

      return (
        <button
          key={b.brand}
          type="button"
          onClick={() => setSelectedBrand(b)}
          title={`${b.brand} | Category: ${b.label} | Merit percentile: ${merit.toFixed(1)} | Visibility index: ${visibility.toFixed(1)} | Gap: ${b.gap != null ? b.gap.toFixed(1) : 'N/A'}`}
          aria-label={`Inspect ${b.brand}, ${b.label}`}
          style={{
            left: `${visibility}%`,
            top: `${100 - merit}%`,
          }}
          className={`absolute -translate-x-1/2 -translate-y-1/2
            w-3 h-3 rounded-full border border-slate-950
            transition-transform hover:scale-150 hover:z-30
            cursor-pointer ${
              dotColors[b.label] ?? 'bg-slate-500'
            } ${
              isSelected
                ? 'ring-4 ring-white scale-150 z-20'
                : ''
            }`}
        />
      );
    })}
</div>


            
        </div>
      </div>

      {/* Search, Filter Tabs & Data Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-slate-800 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2">
            {[
              { id: 'all', label: 'All Brands' },
              { id: 'under-visible', label: 'Under-Visible' },
              { id: 'over-visible', label: 'Over-Visible' },
              { id: 'aligned', label: 'Aligned' },
              { id: 'invisible', label: 'Invisible' },
              { id: 'low-evidence', label: 'Low-Evidence' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedLabel(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedLabel === tab.id
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search brand by name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Brand</th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('label')} className="flex items-center gap-1 hover:text-white">
                    Archetype <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('gap')} className="flex items-center gap-1 hover:text-white">
                    Geo-Gap <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('merit_score')} className="flex items-center gap-1 hover:text-white">
                    Merit Score <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('n_reviews')} className="flex items-center gap-1 hover:text-white">
                    Reviews <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('avg_rating')} className="flex items-center gap-1 hover:text-white">
                    Avg Rating <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('mentions')} className="flex items-center gap-1 hover:text-white">
                    LLM Mentions <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('visibility_index')} className="flex items-center gap-1 hover:text-white">
                    Visibility Index <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredData.slice(0, 50).map((row, index) => {
                const gapNum = row.gap !== null ? row.gap : null;
                const isSelected = selectedBrand?.brand === row.brand;

                return (
                  <tr
                    key={`${row.brand}-${index}`}
                    onClick={() => setSelectedBrand(row)}
                    className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                      isSelected ? 'bg-indigo-950/30' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-semibold text-white">
                      {row.brand}
                    </td>
                    <td className="py-3 px-4">
                      {getLabelBadge(row.label)}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium">
                      {gapNum !== null ? (
                        <span
                          className={
                            gapNum > 25
                              ? 'text-emerald-400 font-bold'
                              : gapNum < -25
                              ? 'text-rose-400 font-bold'
                              : 'text-slate-300'
                          }
                        >
                          {gapNum > 0 ? `+${gapNum.toFixed(1)}` : gapNum.toFixed(1)}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">N/A</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-white">{row.merit_score.toFixed(1)}</span>
                        <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full"
                            style={{ width: `${Math.min(row.merit_score, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {row.n_reviews.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      ★ {row.avg_rating.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <span className={row.mentions > 0 ? 'text-indigo-400 font-bold' : 'text-slate-500'}>
                        {row.mentions}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {row.visibility_index.toFixed(1)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedBrand(row);
                        }}
                        className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filteredData.length === 0 && (
            <div className="py-12 text-center text-slate-500 text-sm">
              No brands match your search criteria.
            </div>
          )}
        </div>
      </div>

      {/* Brand Profile Diagnostics Modal */}
      {selectedBrand && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl relative">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2.5">
                  <h2 className="text-xl font-bold text-white">{selectedBrand.brand}</h2>
                  {getLabelBadge(selectedBrand.label)}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Canonical Brand Key: <span className="font-mono text-slate-300">{selectedBrand.norm_name}</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedBrand(null)}
                className="w-8 h-8 rounded-lg bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center"
              >
                ✕
              </button>
            </div>

            {/* Metrics Breakdown Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-5">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[11px] text-slate-400">Merit Score</div>
                <div className="text-lg font-bold text-white font-mono mt-0.5">
                  {selectedBrand.merit_score.toFixed(1)}
                </div>
                <div className="text-[10px] text-slate-500">Top {selectedBrand.merit_pct.toFixed(0)}% percentile</div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[11px] text-slate-400">Reviews & Rating</div>
                <div className="text-lg font-bold text-white font-mono mt-0.5">
                  {selectedBrand.n_reviews.toLocaleString()}
                </div>
                <div className="text-[10px] text-amber-400">★ {selectedBrand.avg_rating.toFixed(2)} / 5.0</div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[11px] text-slate-400">LLM Mentions</div>
                <div className="text-lg font-bold text-indigo-400 font-mono mt-0.5">
                  {selectedBrand.mentions}
                </div>
                <div className="text-[10px] text-slate-500">Coverage: {(selectedBrand.coverage * 100).toFixed(0)}%</div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[11px] text-slate-400">Geo-Gap Score</div>
                <div className="text-lg font-bold font-mono mt-0.5">
                  {selectedBrand.gap !== null ? (
                    <span className={selectedBrand.gap > 0 ? 'text-emerald-400' : 'text-rose-400'}>
                      {selectedBrand.gap > 0 ? `+${selectedBrand.gap.toFixed(1)}` : selectedBrand.gap.toFixed(1)}
                    </span>
                  ) : (
                    <span className="text-slate-500">N/A</span>
                  )}
                </div>
                <div className="text-[10px] text-slate-500">Merit % - Vis %</div>
              </div>
            </div>

            {/* Tactical GEO Assessment */}
            <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 space-y-3">
              <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-indigo-400" />
                Strategic Generative Engine Optimization (GEO) Audit
              </h4>

              {selectedBrand.label === 'under-visible' && (
                <div className="text-xs text-slate-300 space-y-2">
                  <p>
                    <strong className="text-emerald-400">Massive Discovery Penalty:</strong> Customers genuinely love this brand with {selectedBrand.n_reviews.toLocaleString()} verified reviews and a {selectedBrand.avg_rating.toFixed(2)} rating. However, LLMs only mentioned them {selectedBrand.mentions} times.
                  </p>
                  <div className="bg-emerald-950/20 border border-emerald-900/40 p-2.5 rounded-lg text-emerald-200">
                    <strong>Recommended Actions:</strong>
                    <ul className="list-disc pl-4 mt-1 space-y-0.5 text-slate-300">
                      <li>Increase entity citation co-occurrence on Reddit, Quora, and high-domain editorial beauty roundups.</li>
                      <li>Implement structured JSON-LD Schema.org Product and AggregateRating tags across brand and reseller domains.</li>
                      <li>Seed comparative query benchmarks (e.g. &ldquo;{selectedBrand.brand} vs CeraVe&rdquo;) in public discussion forums.</li>
                    </ul>
                  </div>
                </div>
              )}

              {selectedBrand.label === 'over-visible' && (
                <div className="text-xs text-slate-300 space-y-2">
                  <p>
                    <strong className="text-rose-400">AI Darling / Legacy Marketing Bias:</strong> LLMs mention this brand {selectedBrand.mentions} times with a {selectedBrand.visibility_index.toFixed(1)} visibility index, despite having a lower relative ground-truth merit percentile ({selectedBrand.merit_pct.toFixed(0)}%).
                  </p>
                  <div className="bg-rose-950/20 border border-rose-900/40 p-2.5 rounded-lg text-rose-200">
                    <strong>Vulnerability Warning:</strong>
                    <ul className="list-disc pl-4 mt-1 space-y-0.5 text-slate-300">
                      <li>AI models will increasingly re-weight toward verified real-time purchasing signals and authentic customer satisfaction.</li>
                      <li>Defend sentiment ratios: address negative product feedback before emerging niche brands overtake prompt recommendations.</li>
                    </ul>
                  </div>
                </div>
              )}

              {selectedBrand.label === 'invisible' && (
                <div className="text-xs text-slate-300 space-y-2">
                  <p>
                    <strong className="text-amber-400">Completely Omitted by Generative Engines:</strong> This brand generated {selectedBrand.n_reviews.toLocaleString()} verified reviews on Amazon, yet received 0 mentions across all tested user prompts and personas.
                  </p>
                  <div className="bg-amber-950/20 border border-amber-900/40 p-2.5 rounded-lg text-amber-200">
                    <strong>GEO Recovery Strategy:</strong>
                    <ul className="list-disc pl-4 mt-1 space-y-0.5 text-slate-300">
                      <li>Ensure the brand name is disambiguated and canonicalized without generic prefixes.</li>
                      <li>Build cross-platform web presence beyond marketplace listings so web-crawled LLMs recognize the entity.</li>
                    </ul>
                  </div>
                </div>
              )}

              {selectedBrand.label === 'aligned' && (
                <div className="text-xs text-slate-300">
                  <p>
                    <strong className="text-blue-400">Equilibrium Status:</strong> Generative visibility closely matches actual ground-truth customer satisfaction. Maintain consistent product quality and active digital presence.
                  </p>
                </div>
              )}
            </div>

            <div className="mt-5 flex justify-end">
              <button
                onClick={() => setSelectedBrand(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-medium transition-all"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
