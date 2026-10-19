import React, { useState } from 'react';
import { 
  Sliders, 
  Sparkles, 
  Target, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2, 
  EyeOff, 
  ShieldAlert, 
  Layers,
  ArrowRight
} from 'lucide-react';
import { BrandGapItem } from '../types';

interface GeoGapSimulatorProps {
  existingBrands: BrandGapItem[];
}

export const GeoGapSimulator: React.FC<GeoGapSimulatorProps> = ({
  existingBrands,
}) => {
  const [selectedExisting, setSelectedExisting] = useState<string>('');
  const [brandName, setBrandName] = useState<string>('My Brand');
  const [reviews, setReviews] = useState<number>(3500);
  const [avgRating, setAvgRating] = useState<number>(4.6);
  const [positiveSentiment, setPositiveSentiment] = useState<number>(88);
  const [mentions, setMentions] = useState<number>(2);
  const [avgPosition, setAvgPosition] = useState<number>(4.5);
  const [coveragePct, setCoveragePct] = useState<number>(15);

  const handleSelectExisting = (brandName: string) => {
    setSelectedExisting(brandName);
    const item = existingBrands.find((b) => b.brand === brandName);
    if (item) {
      setBrandName(item.brand);
      setReviews(item.n_reviews);
      setAvgRating(item.avg_rating);
      setMentions(item.mentions);
      setAvgPosition(item.avg_rank || 5);
      setCoveragePct(Math.round(item.coverage * 100));
    }
  };

  // Mathematical simulation of Ground Truth Merit & LLM Visibility
  // Ground truth merit percentile (based on empirical distribution)
  const simulatedMeritPercentile = Math.min(
    Math.max(
      Math.round(
        (Math.log10(Math.max(reviews, 10)) / 4.5) * 45 +
        ((avgRating - 3.5) / 1.5) * 45 +
        ((positiveSentiment - 50) / 50) * 10
      ),
      5
    ),
    99
  );

  // Visibility Index: (mentions * coverage) / avgPosition
  const rawVis = mentions > 0 ? (mentions * (coveragePct / 100)) / Math.max(avgPosition, 1) : 0;
  // Scaled visibility percentile approx (in empirical set, CeraVe raw vis was ~28 yielding 100 index)
  const simulatedVisPercentile = Math.min(Math.round((rawVis / 28) * 100), 100);

  // Geo-Gap calculation
  const isReliable = mentions > 0 && reviews >= 1000;
  const isLowEvidence = mentions > 0 && reviews < 1000;
  const isZeroMentions = mentions === 0;

  const gapScore = simulatedMeritPercentile - simulatedVisPercentile;

  let archetype: 'under-visible' | 'over-visible' | 'aligned' | 'invisible' | 'low-evidence' = 'aligned';
  if (isZeroMentions) {
    archetype = 'invisible';
  } else if (isLowEvidence) {
    archetype = 'low-evidence';
  } else if (gapScore > 25) {
    archetype = 'under-visible';
  } else if (gapScore < -25) {
    archetype = 'over-visible';
  } else {
    archetype = 'aligned';
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            Interactive GEO Brand Audit & Gap Simulator
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Simulate how market purchasing proof and LLM recommendation frequency interact to produce your Generative Engine Gap score.
          </p>
        </div>

        {/* Quick Load Preset */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400">Load Preset:</label>
          <select
            value={selectedExisting}
            onChange={(e) => handleSelectExisting(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 max-w-xs"
          >
            <option value="">-- Choose Existing Brand --</option>
            {existingBrands.slice(0, 30).map((b) => (
              <option key={b.brand} value={b.brand}>
                {b.brand} ({b.label})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Inputs */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2 pb-2 border-b border-slate-800">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              1. Ground-Truth Consumer Proof Signals
            </h3>

            <div>
              <label className="text-xs text-slate-300 font-medium block mb-1">Brand Name</label>
              <input
                type="text"
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-300 font-medium block mb-1">
                  Customer Reviews ({reviews.toLocaleString()})
                </label>
                <input
                  type="range"
                  min="50"
                  max="50000"
                  step="50"
                  value={reviews}
                  onChange={(e) => setReviews(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium block mb-1">
                  Avg Rating (★ {avgRating.toFixed(2)})
                </label>
                <input
                  type="range"
                  min="3.0"
                  max="5.0"
                  step="0.05"
                  value={avgRating}
                  onChange={(e) => setAvgRating(Number(e.target.value))}
                  className="w-full accent-amber-400"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-300 font-medium block mb-1">
                Positive Sentiment Ratio ({positiveSentiment}%)
              </label>
              <input
                type="range"
                min="30"
                max="100"
                step="1"
                value={positiveSentiment}
                onChange={(e) => setPositiveSentiment(Number(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2 pb-2 border-b border-slate-800">
              <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
              2. Generative Engine Probing Signals
            </h3>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-slate-300 font-medium block mb-1">
                  LLM Mentions ({mentions})
                </label>
                <input
                  type="range"
                  min="0"
                  max="35"
                  step="1"
                  value={mentions}
                  onChange={(e) => setMentions(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium block mb-1">
                  Avg Position (#{avgPosition.toFixed(1)})
                </label>
                <input
                  type="range"
                  min="1.0"
                  max="10.0"
                  step="0.1"
                  value={avgPosition}
                  onChange={(e) => setAvgPosition(Number(e.target.value))}
                  className="w-full accent-cyan-400"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium block mb-1">
                  Query Coverage ({coveragePct}%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={coveragePct}
                  onChange={(e) => setCoveragePct(Number(e.target.value))}
                  className="w-full accent-indigo-400"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Output Diagnostic Card */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="text-xs text-slate-400 font-medium">Diagnostic Target</div>
                <h3 className="text-xl font-bold text-white mt-0.5">{brandName}</h3>
              </div>

              <div>
                {archetype === 'under-visible' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    <TrendingUp className="w-4 h-4" /> Under-Visible Archetype
                  </span>
                )}
                {archetype === 'over-visible' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    <AlertCircle className="w-4 h-4" /> Over-Visible Archetype
                  </span>
                )}
                {archetype === 'invisible' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    <EyeOff className="w-4 h-4" /> Invisible Archetype
                  </span>
                )}
                {archetype === 'aligned' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    <CheckCircle2 className="w-4 h-4" /> Aligned Archetype
                  </span>
                )}
                {archetype === 'low-evidence' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-500/20 text-slate-300 border border-slate-600/30">
                    <ShieldAlert className="w-4 h-4" /> Low-Evidence Mention
                  </span>
                )}
              </div>
            </div>

            {/* Score Comparison Bars */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                <div className="text-[11px] text-slate-400">Merit Percentile</div>
                <div className="text-2xl font-bold text-cyan-400 font-mono mt-1">
                  {simulatedMeritPercentile}%
                </div>
                <div className="text-[10px] text-slate-500">True Consumer Proof</div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                <div className="text-[11px] text-slate-400">AI Visibility Index</div>
                <div className="text-2xl font-bold text-indigo-400 font-mono mt-1">
                  {simulatedVisPercentile}
                </div>
                <div className="text-[10px] text-slate-500">Generative Share</div>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                <div className="text-[11px] text-slate-400">Geo-Gap Score</div>
                <div
                  className={`text-2xl font-bold font-mono mt-1 ${
                    gapScore > 25
                      ? 'text-emerald-400'
                      : gapScore < -25
                      ? 'text-rose-400'
                      : 'text-blue-400'
                  }`}
                >
                  {isZeroMentions ? 'N/A' : gapScore > 0 ? `+${gapScore}` : gapScore}
                </div>
                <div className="text-[10px] text-slate-500">Merit % - Vis %</div>
              </div>
            </div>

            {/* Tactical Action Plan */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Customized GEO Action Plan
              </h4>

              {archetype === 'under-visible' && (
                <div className="text-xs text-slate-300 space-y-2">
                  <p className="text-emerald-300 font-medium">
                    Priority: Unlock LLM Discovery to capture high-intent buyers.
                  </p>
                  <ul className="space-y-1 text-slate-400">
                    <li className="flex items-start gap-2">
                      <ArrowRight className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      Build editorial entity co-citations in high-authority buying guides and Reddit discussions.
                    </li>
                    <li className="flex items-start gap-2">
                      <ArrowRight className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      Implement JSON-LD Product & Review structured data across your root domain.
                    </li>
                    <li className="flex items-start gap-2">
                      <ArrowRight className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      Publish head-to-head comparison matrices with entrenched category incumbents.
                    </li>
                  </ul>
                </div>
              )}

              {archetype === 'over-visible' && (
                <div className="text-xs text-slate-300 space-y-2">
                  <p className="text-rose-300 font-medium">
                    Priority: Fortify customer sentiment against real-time AI recalibration.
                  </p>
                  <ul className="space-y-1 text-slate-400">
                    <li className="flex items-start gap-2">
                      <ArrowRight className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                      Audit recent 1-star reviews on formula changes, scent, or packaging defects.
                    </li>
                    <li className="flex items-start gap-2">
                      <ArrowRight className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                      Generative search engines are integrating live marketplace ratings; poor sentiment will erode this advantage.
                    </li>
                  </ul>
                </div>
              )}

              {archetype === 'invisible' && (
                <div className="text-xs text-slate-300 space-y-2">
                  <p className="text-amber-300 font-medium">
                    Priority: Break zero-visibility barrier by establishing crawlable digital identity.
                  </p>
                  <ul className="space-y-1 text-slate-400">
                    <li className="flex items-start gap-2">
                      <ArrowRight className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                      LLMs have zero training presence or indexation for this brand name.
                    </li>
                    <li className="flex items-start gap-2">
                      <ArrowRight className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                      Deploy a brand knowledge graph node (Wikidata, Crunchbase, verified retailer listings).
                    </li>
                  </ul>
                </div>
              )}

              {archetype === 'aligned' && (
                <div className="text-xs text-slate-300 space-y-2">
                  <p className="text-blue-300 font-medium">
                    Priority: Maintain optimal equilibrium and monitor competitor shifts.
                  </p>
                  <p className="text-slate-400">
                    Your consumer proof and AI engine presence are well-balanced. Keep monitoring quarterly intent probing runs.
                  </p>
                </div>
              )}

              {archetype === 'low-evidence' && (
                <div className="text-xs text-slate-300 space-y-2">
                  <p className="text-slate-300 font-medium">
                    Priority: Scale verified consumer reviews to back up AI claims.
                  </p>
                  <p className="text-slate-400">
                    LLMs recommend this brand, but customer review volume on Amazon is below the 1,000 threshold for statistical reliability.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
