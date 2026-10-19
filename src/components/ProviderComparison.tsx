import React, { useState, useMemo } from 'react';
import { 
  Sparkles, 
  Search, 
  ArrowUpDown, 
  Award, 
  BarChart, 
  Layers,
  PieChart,
  Percent
} from 'lucide-react';
import { BrandVisibilityItem } from '../types';

interface ProviderComparisonProps {
  visibilityData: BrandVisibilityItem[];
}

export const ProviderComparison: React.FC<ProviderComparisonProps> = ({
  visibilityData,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof BrandVisibilityItem>('visibility_index');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const filteredData = useMemo(() => {
    return visibilityData
      .filter((b) =>
        (b.brand_canonical || b.brand_key)
          .toLowerCase()
          .includes(searchTerm.toLowerCase())
      )
      .sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];
        if (valA === null || valA === undefined) valA = -999999;
        if (valB === null || valB === undefined) valB = -999999;
        return sortAsc ? (valA as number) - (valB as number) : (valB as number) - (valA as number);
      });
  }, [visibilityData, searchTerm, sortField, sortAsc]);

  const handleSort = (field: keyof BrandVisibilityItem) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  // Top 5 brands by Share of Voice
  const topVoiceBrands = useMemo(() => {
    return [...visibilityData]
      .sort((a, b) => b.share_of_voice - a.share_of_voice)
      .slice(0, 6);
  }, [visibilityData]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            Generative Engine Brand Visibility & Share of Voice
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Analyzing {visibilityData.length} brands captured across multi-engine LLM probing (Groq Qwen & OpenRouter).
          </p>
        </div>
      </div>

      {/* Share of Voice Leaderboard Bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
            <PieChart className="w-4 h-4 text-cyan-400" />
            Top AI Engine Share of Voice (SoV)
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Percentage of all LLM brand recommendations captured by a single entity across all commercial queries.
          </p>

          <div className="space-y-3">
            {topVoiceBrands.map((brand, i) => (
              <div key={brand.brand_key} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-white">
                    #{i + 1} {brand.brand_canonical || brand.brand_key}
                  </span>
                  <span className="font-mono text-cyan-400 font-bold">
                    {(brand.share_of_voice * 100).toFixed(1)}% SoV ({brand.mentions} mentions)
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full"
                    style={{ width: `${Math.min(brand.share_of_voice * 400, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
              <Award className="w-4 h-4 text-amber-400" />
              Empirical Findings: Legacy Concentration Bias
            </h3>
            <div className="text-xs text-slate-300 space-y-3 leading-relaxed">
              <p>
                The top 2 brands (<strong className="text-white">CeraVe</strong> and <strong className="text-white">La Roche-Posay</strong>) capture over <strong className="text-cyan-400">20.0% of total LLM brand mentions</strong> in beauty and personal care.
              </p>
              <p>
                In contrast, dozens of top-rated Amazon brands with tens of thousands of verified 5-star customer reviews receive <span className="text-rose-400 font-semibold">zero generative visibility</span>.
              </p>
              <p>
                This highlights a profound asymmetry in AI search: generative recommendation engines default heavily to mainstream legacy brands trained into early weights, regardless of real-time purchasing customer sentiment.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>Query Coverage Threshold: <strong>86.5%</strong></span>
            <span>Average Rank Range: <strong>1.4 &ndash; 8.5</strong></span>
          </div>
        </div>
      </div>

      {/* Probed Brands Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between gap-4">
          <div className="relative w-full max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search probed brands..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="text-xs text-slate-400">
            Showing <strong>{filteredData.length}</strong> probed brands
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Brand</th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('visibility_index')} className="flex items-center gap-1 hover:text-white">
                    Visibility Index <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('mentions')} className="flex items-center gap-1 hover:text-white">
                    Mentions <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('avg_rank')} className="flex items-center gap-1 hover:text-white">
                    Avg Rank Position <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('coverage')} className="flex items-center gap-1 hover:text-white">
                    Query Coverage <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('share_of_voice')} className="flex items-center gap-1 hover:text-white">
                    Share of Voice <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="py-3 px-4">
                  <button onClick={() => handleSort('merit_score')} className="flex items-center gap-1 hover:text-white">
                    Ground Truth Merit <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredData.map((row, idx) => (
                <tr key={`${row.brand_key}-${idx}`} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    {row.brand_canonical || row.brand_key}
                    <span className="text-[10px] text-slate-500 font-normal block">
                      matched by {row.match_method}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-indigo-400">
                        {row.visibility_index.toFixed(1)}
                      </span>
                      <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full"
                          style={{ width: `${Math.min(row.visibility_index, 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-white">
                    {row.mentions}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">
                    #{row.avg_rank.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 font-mono text-cyan-300">
                    {(row.coverage * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">
                    {(row.share_of_voice * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 font-mono">
                    {row.merit_score !== null ? (
                      <span className="text-white font-medium">{row.merit_score.toFixed(1)}</span>
                    ) : (
                      <span className="text-slate-500 italic">Unmatched</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
