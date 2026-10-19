import React, { useState, useMemo } from 'react';
import { 
  TrendingUp, 
  Calendar, 
  Star, 
  MessageSquare, 
  Smile, 
  ChevronDown 
} from 'lucide-react';
import { MonthlyTrendItem } from '../types';

interface TrendsViewProps {
  trends: MonthlyTrendItem[];
  category: string;
}

export const TrendsView: React.FC<TrendsViewProps> = ({
  trends,
  category,
}) => {
  const [yearFilter, setYearFilter] = useState<string>('all');

  const categoryTrends = useMemo(() => {
    return trends.filter((t) => t.category === category);
  }, [trends, category]);

  // Extract available years
  const availableYears = useMemo(() => {
    const years = new Set<string>();
    categoryTrends.forEach((t) => {
      const year = t.month.split('-')[0];
      if (year) years.add(year);
    });
    return Array.from(years).sort().reverse();
  }, [categoryTrends]);

  // Filtered by year if chosen
  const filteredTrends = useMemo(() => {
    if (yearFilter === 'all') return categoryTrends;
    return categoryTrends.filter((t) => t.month.startsWith(yearFilter));
  }, [categoryTrends, yearFilter]);

  // Aggregate stats
  const aggregateStats = useMemo(() => {
    if (categoryTrends.length === 0) return { totalReviews: 0, avgRating: 0, avgSentiment: 0 };
    const totalReviews = categoryTrends.reduce((acc, curr) => acc + curr.n_reviews, 0);
    const avgRating =
      categoryTrends.reduce((acc, curr) => acc + curr.avg_rating * curr.n_reviews, 0) /
      Math.max(totalReviews, 1);
    const avgSentiment =
      categoryTrends.reduce((acc, curr) => acc + curr.avg_sentiment * curr.n_reviews, 0) /
      Math.max(totalReviews, 1);

    return { totalReviews, avgRating, avgSentiment };
  }, [categoryTrends]);

  // Pick recent 24 months for visual chart
  const recentTimeline = useMemo(() => {
    return [...categoryTrends].slice(-24);
  }, [categoryTrends]);

  const maxMonthReviews = useMemo(() => {
    return Math.max(...recentTimeline.map((t) => t.n_reviews), 1);
  }, [recentTimeline]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-400" />
            Historical Category Review & Sentiment Trends
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tracking customer purchase volume, satisfaction ratings, and NLP sentiment trajectories over two decades.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400">Filter Year:</label>
          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Historical (2000 - Present)</option>
            {availableYears.map((yr) => (
              <option key={yr} value={yr}>
                {yr}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Aggregate Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <MessageSquare className="w-4 h-4 text-cyan-400" />
            Tracked Review Volume
          </div>
          <div className="text-2xl font-bold text-white font-mono mt-1">
            {aggregateStats.totalReviews.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">In {category.replace(/_/g, ' ')} dataset</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Star className="w-4 h-4 text-amber-400" />
            Historical Average Rating
          </div>
          <div className="text-2xl font-bold text-amber-300 font-mono mt-1">
            ★ {aggregateStats.avgRating.toFixed(2)} / 5.0
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Volume-weighted consumer score</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Smile className="w-4 h-4 text-emerald-400" />
            Average Sentiment Index
          </div>
          <div className="text-2xl font-bold text-emerald-300 font-mono mt-1">
            +{(aggregateStats.avgSentiment * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-500 mt-1">VADER / RoBERTa polarity score</div>
        </div>
      </div>

      {/* Recent 24 Months Timeline Visualizer */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <h3 className="text-sm font-semibold text-white mb-2">
          Monthly Review Volume Dynamics (Recent 24 Periods)
        </h3>
        <p className="text-xs text-slate-400 mb-5">
          Bars represent relative review count per month. Hover over any bar to view review volume and rating.
        </p>

        <div className="h-48 flex items-end gap-1.5 sm:gap-2 px-2 pb-2 border-b border-slate-800">
          {recentTimeline.map((item) => {
            const heightPct = Math.max((item.n_reviews / maxMonthReviews) * 100, 6);
            return (
              <div
                key={item.month}
                className="flex-1 flex flex-col items-center group relative h-full justify-end"
              >
                {/* Tooltip */}
                <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950 border border-slate-700 text-white text-[10px] rounded px-2 py-1 pointer-events-none whitespace-nowrap z-20 shadow-lg">
                  <div><strong>{item.month}</strong></div>
                  <div>{item.n_reviews.toLocaleString()} reviews | ★ {item.avg_rating.toFixed(2)}</div>
                </div>

                {/* Bar */}
                <div
                  className="w-full rounded-t-sm bg-gradient-to-t from-indigo-600 to-cyan-400 group-hover:from-indigo-500 group-hover:to-cyan-300 transition-all cursor-pointer"
                  style={{ height: `${heightPct}%` }}
                />
              </div>
            );
          })}
        </div>

        <div className="flex justify-between text-[11px] text-slate-500 mt-2 px-2">
          <span>{recentTimeline[0]?.month || 'Start'}</span>
          <span>Timeline Progression</span>
          <span>{recentTimeline[recentTimeline.length - 1]?.month || 'End'}</span>
        </div>
      </div>

      {/* Monthly Records Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex justify-between items-center text-xs">
          <span className="font-semibold text-white">Monthly Records Archive</span>
          <span className="text-slate-400">{filteredTrends.length} months listed</span>
        </div>
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800 sticky top-0">
              <tr>
                <th className="py-2.5 px-4">Period Month</th>
                <th className="py-2.5 px-4">Review Volume</th>
                <th className="py-2.5 px-4">Average Rating</th>
                <th className="py-2.5 px-4">Sentiment Polarity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredTrends.slice(0, 60).map((t) => (
                <tr key={t.month} className="hover:bg-slate-800/40">
                  <td className="py-2.5 px-4 font-mono font-medium text-white">{t.month}</td>
                  <td className="py-2.5 px-4 font-mono text-slate-300">{t.n_reviews.toLocaleString()}</td>
                  <td className="py-2.5 px-4 font-mono text-amber-300">★ {t.avg_rating.toFixed(2)}</td>
                  <td className="py-2.5 px-4 font-mono text-emerald-300">
                    +{(t.avg_sentiment * 100).toFixed(1)}%
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
