import React, { useState, useMemo } from 'react';
import { 
  Trophy, 
  Search, 
  ShoppingBag, 
  Sparkles, 
  ArrowUpDown, 
  ExternalLink,
  ThumbsUp,
  Clock,
  Star
} from 'lucide-react';
import { LeaderboardBrandItem, LeaderboardProductItem } from '../types';

interface LeaderboardsViewProps {
  brands: LeaderboardBrandItem[];
  products: LeaderboardProductItem[];
  category: string;
}

export const LeaderboardsView: React.FC<LeaderboardsViewProps> = ({
  brands,
  products,
  category,
}) => {
  const [viewType, setViewType] = useState<'brands' | 'products'>('brands');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<string>('rank');
  const [sortAsc, setSortAsc] = useState<boolean>(true);

  // Filter by category
  const filteredBrands = useMemo(() => {
    return brands
      .filter((b) => b.category === category)
      .filter((b) => b.brand_canonical.toLowerCase().includes(searchTerm.toLowerCase()))
      .sort((a, b) => {
        const valA = (a as any)[sortField];
        const valB = (b as any)[sortField];
        return sortAsc ? valA - valB : valB - valA;
      });
  }, [brands, category, searchTerm, sortField, sortAsc]);

  const filteredProducts = useMemo(() => {
    return products
      .filter((p) => p.category === category)
      .filter(
        (p) =>
          p.product_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.store.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.parent_asin.toLowerCase().includes(searchTerm.toLowerCase())
      )
      .sort((a, b) => {
        const valA = (a as any)[sortField];
        const valB = (b as any)[sortField];
        return sortAsc ? valA - valB : valB - valA;
      });
  }, [products, category, searchTerm, sortField, sortAsc]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === 'rank' ? true : false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Toggle */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-xl">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-400" />
            Ground-Truth Consumer Merit Leaderboards
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Calculated from 24.3M verified reviews, combining Bayesian rating, recency momentum, and NLP sentiment polarity.
          </p>
        </div>

        <div className="flex items-center bg-slate-950 border border-slate-800 p-1 rounded-xl">
          <button
            onClick={() => {
              setViewType('brands');
              setSortField('rank');
              setSortAsc(true);
            }}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewType === 'brands'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Top Brands ({filteredBrands.length})
          </button>
          <button
            onClick={() => {
              setViewType('products');
              setSortField('rank');
              setSortAsc(true);
            }}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewType === 'products'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Top Products ({filteredProducts.length})
          </button>
        </div>
      </div>

      {/* Search and Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between gap-4">
          <div className="relative w-full max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder={`Search ${viewType === 'brands' ? 'brands...' : 'products, store or ASIN...'}`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="text-xs text-slate-400">
            Category: <strong className="text-indigo-300">{category.replace(/_/g, ' ')}</strong>
          </div>
        </div>

        {/* Brand Leaderboard Table */}
        {viewType === 'brands' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">
                    <button onClick={() => handleSort('rank')} className="flex items-center gap-1 hover:text-white">
                      Rank <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="py-3 px-4">Brand</th>
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
                    <button onClick={() => handleSort('recency_weighted_rating')} className="flex items-center gap-1 hover:text-white">
                      Recency Rating <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="py-3 px-4">
                    <button onClick={() => handleSort('pct_positive')} className="flex items-center gap-1 hover:text-white">
                      Sentiment Polarity <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredBrands.map((b) => (
                  <tr key={b.rank} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-white">
                      #{b.rank}
                    </td>
                    <td className="py-3 px-4 font-semibold text-white">
                      {b.brand_canonical}
                      <span className="text-[10px] text-slate-500 font-normal block">
                        {b.n_products} active product{b.n_products > 1 ? 's' : ''}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-indigo-400">
                          {b.merit_score.toFixed(1)}
                        </span>
                        <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full"
                            style={{ width: `${Math.min(b.merit_score, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {b.n_reviews.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      ★ {b.avg_rating.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      ★ {b.recency_weighted_rating.toFixed(2)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="w-32">
                        <div className="flex justify-between text-[10px] font-mono mb-1">
                          <span className="text-emerald-400">{(b.pct_positive * 100).toFixed(0)}% pos</span>
                          <span className="text-rose-400">{(b.pct_negative * 100).toFixed(0)}% neg</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-slate-800 flex overflow-hidden">
                          <div
                            className="bg-emerald-500 h-full"
                            style={{ width: `${b.pct_positive * 100}%` }}
                          />
                          <div
                            className="bg-slate-600 h-full"
                            style={{ width: `${b.pct_neutral * 100}%` }}
                          />
                          <div
                            className="bg-rose-500 h-full"
                            style={{ width: `${b.pct_negative * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Product Leaderboard Table */
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">
                    <button onClick={() => handleSort('rank')} className="flex items-center gap-1 hover:text-white">
                      Rank <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="py-3 px-4">Product Title</th>
                  <th className="py-3 px-4">Store</th>
                  <th className="py-3 px-4">
                    <button onClick={() => handleSort('merit_score')} className="flex items-center gap-1 hover:text-white">
                      Merit <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="py-3 px-4">
                    <button onClick={() => handleSort('n_reviews')} className="flex items-center gap-1 hover:text-white">
                      Reviews <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="py-3 px-4">Rating</th>
                  <th className="py-3 px-4">Sentiment Distribution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredProducts.map((p) => (
                  <tr key={p.rank} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-white">
                      #{p.rank}
                    </td>
                    <td className="py-3 px-4 max-w-xs sm:max-w-md">
                      <div className="font-semibold text-white line-clamp-1">{p.product_title}</div>
                      <span className="text-[10px] text-slate-500 font-mono">ASIN: {p.parent_asin}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-medium">
                      {p.store || <span className="text-slate-500 italic">Direct</span>}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-indigo-400">
                      {p.merit_score.toFixed(1)}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {p.n_reviews.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      ★ {p.avg_rating.toFixed(2)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="w-28">
                        <div className="flex justify-between text-[10px] font-mono mb-1">
                          <span className="text-emerald-400">{(p.pct_positive * 100).toFixed(0)}%</span>
                          <span className="text-rose-400">{(p.pct_negative * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-slate-800 flex overflow-hidden">
                          <div
                            className="bg-emerald-500 h-full"
                            style={{ width: `${p.pct_positive * 100}%` }}
                          />
                          <div
                            className="bg-slate-600 h-full"
                            style={{ width: `${p.pct_neutral * 100}%` }}
                          />
                          <div
                            className="bg-rose-500 h-full"
                            style={{ width: `${p.pct_negative * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
