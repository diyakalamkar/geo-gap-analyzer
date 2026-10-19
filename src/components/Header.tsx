import React from 'react';
import { 
  BarChart3, 
  Target, 
  Trophy, 
  Sparkles, 
  TrendingUp, 
  Sliders, 
  Cpu, 
  Layers,
  ShieldCheck
} from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  selectedCategory: string;
  setSelectedCategory: (cat: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  selectedCategory,
  setSelectedCategory,
}) => {
  const tabs = [
    { id: 'explorer', label: 'Geo-Gap Explorer', icon: Target },
    { id: 'leaderboards', label: 'Merit Leaderboards', icon: Trophy },
    { id: 'probing', label: 'LLM Probing Lab', icon: Cpu },
    { id: 'comparison', label: 'Provider Benchmark', icon: Sparkles },
    { id: 'trends', label: 'Category Trends', icon: TrendingUp },
    { id: 'simulator', label: 'GEO Audit Simulator', icon: Sliders },
    { id: 'validation', label: 'Validation', icon: ShieldCheck },
  ];

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 p-0.5 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  Geo-Gap Analyzer
                </span>
                <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  GEO Intelligence
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Ground-Truth Consumer Merit vs Generative Engine Visibility
              </p>
            </div>
          </div>

          {/* Category Switcher & Stats pill */}
          <div className="flex items-center gap-3">
            <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-1 text-xs">
              <button
                onClick={() => setSelectedCategory('All_Beauty')}
                className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                  selectedCategory === 'All_Beauty'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                All Beauty
              </button>
              <button
                onClick={() => setSelectedCategory('Beauty_and_Personal_Care')}
                className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                  selectedCategory === 'Beauty_and_Personal_Care'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Personal Care
              </button>
            </div>

            <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span><strong>24.3M</strong> Reviews Analyzed</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto py-2 no-scrollbar border-t border-slate-800/60">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium whitespace-nowrap transition-all duration-200 ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
