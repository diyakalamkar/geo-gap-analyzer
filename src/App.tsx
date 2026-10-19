import React, { useState } from 'react';
import { Header } from './components/Header';
import { GeoGapExplorer } from './components/GeoGapExplorer';
import { LeaderboardsView } from './components/LeaderboardsView';
import { ProbingLab } from './components/ProbingLab';
import { ProviderComparison } from './components/ProviderComparison';
import { TrendsView } from './components/TrendsView';
import { GeoGapSimulator } from './components/GeoGapSimulator';
import { ValidationView } from './components/ValidationView';

// Person 3's validated outputs are generated from P3_visibility_gap_results.xlsx
// by scripts/export_p3_data.py before Vite starts.
import brandGapRaw from './data/p3BrandGap.json';
import brandVisibilityRaw from './data/p3BrandVisibility.json';
import validationRaw from './data/p3Validation.json';

// Existing supporting views retain their existing source datasets.
import leaderboardBrandsRaw from './data/leaderboardBrands.json';
import leaderboardProductsRaw from './data/leaderboardProducts.json';
import monthlyTrendsRaw from './data/monthlyTrends.json';
import probingResponsesRaw from './data/probingResponses.json';
import rejectedEntitiesRaw from './data/rejectedEntities.json';

import {
  BrandGapItem,
  BrandVisibilityItem,
  LeaderboardBrandItem,
  LeaderboardProductItem,
  MonthlyTrendItem,
  ProbingResponseItem,
  RejectedEntityItem,
} from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('explorer');
  const [selectedCategory, setSelectedCategory] = useState<string>('All_Beauty');

  const brandGap = brandGapRaw as unknown as BrandGapItem[];
  const brandVisibility = brandVisibilityRaw as unknown as BrandVisibilityItem[];
  const leaderboardBrands = leaderboardBrandsRaw as unknown as LeaderboardBrandItem[];
  const leaderboardProducts = leaderboardProductsRaw as unknown as LeaderboardProductItem[];
  const monthlyTrends = monthlyTrendsRaw as unknown as MonthlyTrendItem[];
  const probingResponses = probingResponsesRaw as unknown as ProbingResponseItem[];
  const rejectedEntities = rejectedEntitiesRaw as unknown as RejectedEntityItem[];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
      />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'explorer' && <GeoGapExplorer data={brandGap} />}
        {activeTab === 'leaderboards' && (
          <LeaderboardsView brands={leaderboardBrands} products={leaderboardProducts} category={selectedCategory} />
        )}
        {activeTab === 'probing' && (
          <ProbingLab responses={probingResponses} rejectedEntities={rejectedEntities} />
        )}
        {activeTab === 'comparison' && <ProviderComparison visibilityData={brandVisibility} />}
        {activeTab === 'trends' && <TrendsView trends={monthlyTrends} category={selectedCategory} />}
        {activeTab === 'simulator' && <GeoGapSimulator existingBrands={brandGap} />}
        {activeTab === 'validation' && <ValidationView data={validationRaw} />}
      </main>
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span><strong>Geo-Gap Analyzer</strong> &mdash; Generative Engine Optimization Diagnostics Platform</span>
          <span className="font-mono text-[11px] text-slate-400">Person 3 visibility and gap results · 37 valid responses</span>
        </div>
      </footer>
    </div>
  );
}
