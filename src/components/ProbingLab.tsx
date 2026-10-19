import React, { useState } from 'react';
import { 
  Cpu, 
  Terminal, 
  Filter, 
  Bot, 
  UserCheck, 
  Sparkles, 
  FileText, 
  AlertTriangle,
  CheckCircle,
  Copy,
  Layers
} from 'lucide-react';
import { ProbingResponseItem, RejectedEntityItem } from '../types';

interface ProbingLabProps {
  responses: ProbingResponseItem[];
  rejectedEntities: RejectedEntityItem[];
}

export const ProbingLab: React.FC<ProbingLabProps> = ({
  responses,
  rejectedEntities,
}) => {
  const [selectedSubTab, setSelectedSubTab] = useState<'probes' | 'cleaning'>('probes');
  const [selectedPersona, setSelectedPersona] = useState<string>('all');
  const [selectedIntent, setSelectedIntent] = useState<string>('all');
  const [activeResponseIndex, setActiveResponseIndex] = useState<number>(0);
  const [copied, setCopied] = useState<boolean>(false);

  const personas = ['all', 'general', 'budget_conscious', 'beginner', 'sensitive_skin'];
  const intents = ['all', 'category_discovery', 'product_recommendation', 'comparison', 'brand_discovery', 'problem_based'];

  const filteredResponses = responses.filter((r) => {
    const matchPersona = selectedPersona === 'all' || r.persona === selectedPersona;
    const matchIntent = selectedIntent === 'all' || r.intent === selectedIntent;
    return matchPersona && matchIntent;
  });

  const activeResponse = filteredResponses[activeResponseIndex] || filteredResponses[0] || responses[0];

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            LLM Probing Laboratory & Entity Extraction
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Empirical evaluation across Groq (Qwen) & OpenRouter LLM engines with varying buyer personas and commercial intents.
          </p>
        </div>

        <div className="flex items-center bg-slate-950 border border-slate-800 p-1 rounded-xl">
          <button
            onClick={() => setSelectedSubTab('probes')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              selectedSubTab === 'probes'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Probe Responses ({responses.length})
          </button>
          <button
            onClick={() => setSelectedSubTab('cleaning')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              selectedSubTab === 'cleaning'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Normalization & Hallucination Filter ({rejectedEntities.length})
          </button>
        </div>
      </div>

      {selectedSubTab === 'probes' ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Probe Selector & Filters */}
          <div className="lg:col-span-5 space-y-4">
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <Filter className="w-4 h-4 text-indigo-400" />
                Filter by Intent & Persona
              </div>

              {/* Persona Filter */}
              <div>
                <label className="text-[11px] text-slate-400 font-medium block mb-1">Buyer Persona</label>
                <div className="flex flex-wrap gap-1.5">
                  {personas.map((p) => (
                    <button
                      key={p}
                      onClick={() => {
                        setSelectedPersona(p);
                        setActiveResponseIndex(0);
                      }}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                        selectedPersona === p
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white'
                      }`}
                    >
                      {p.replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Intent Filter */}
              <div>
                <label className="text-[11px] text-slate-400 font-medium block mb-1">Commercial Intent</label>
                <div className="flex flex-wrap gap-1.5">
                  {intents.map((i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setSelectedIntent(i);
                        setActiveResponseIndex(0);
                      }}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                        selectedIntent === i
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white'
                      }`}
                    >
                      {i.replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Response List */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-xl max-h-[500px] overflow-y-auto divide-y divide-slate-800/80">
              {filteredResponses.map((item, idx) => {
                const isSelected = activeResponse?.prompt_id === item.prompt_id;
                return (
                  <div
                    key={`${item.prompt_id}-${idx}`}
                    onClick={() => setActiveResponseIndex(idx)}
                    className={`p-3.5 cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-indigo-950/40 border-l-4 border-indigo-500'
                        : 'hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-white uppercase tracking-wider text-[10px] bg-slate-800 px-2 py-0.5 rounded">
                        {item.provider} • {item.model}
                      </span>
                      <span className="text-[11px] font-mono text-indigo-400">
                        {item.persona.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div className="text-xs text-slate-300 font-medium line-clamp-2">
                      &ldquo;{item.prompt.split('\n')[0]}&rdquo;
                    </div>
                    <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-500 font-mono">
                      <span>ID: {item.query_id}</span>
                      <span>Target Brands: {item.target_brands?.length || 0}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Response Inspector & Extracted Brands */}
          <div className="lg:col-span-7 space-y-4">
            {activeResponse ? (
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
                {/* Prompt Info Header */}
                <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 text-xs font-semibold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {activeResponse.provider.toUpperCase()}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        {activeResponse.model}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      Query ID: <code className="text-white">{activeResponse.query_id}</code> | Persona: <strong className="text-indigo-300">{activeResponse.persona}</strong>
                    </div>
                  </div>

                  <button
                    onClick={() => handleCopy(activeResponse.response_text)}
                    className="flex items-center gap-1 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition-all"
                  >
                    {copied ? <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied' : 'Copy Response'}</span>
                  </button>
                </div>

                {/* Prompt Card */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                    Probe Prompt Sent
                  </div>
                  <pre className="text-xs text-slate-200 font-sans whitespace-pre-wrap">
                    {activeResponse.prompt}
                  </pre>
                </div>

                {/* Target Brands being tested */}
                {activeResponse.target_brands && activeResponse.target_brands.length > 0 && (
                  <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Ground-Truth Target Brands Under Test ({activeResponse.target_brands.length})
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {activeResponse.target_brands.slice(0, 15).map((b, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-slate-800/80 border border-slate-700/60 rounded text-[11px] text-slate-300"
                        >
                          {b}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Raw LLM Response */}
                <div>
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Bot className="w-3.5 h-3.5 text-cyan-400" />
                    Raw LLM Generative Response
                  </div>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs text-slate-300 max-h-96 overflow-y-auto whitespace-pre-wrap leading-relaxed font-sans">
                    {activeResponse.response_text}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500">
                Select a probe query from the list to view the response.
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Normalization & Hallucination Filter Sub-Tab */
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="border-b border-slate-800 pb-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Entity Disambiguation & Hallucination Defense Engine
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              LLMs frequently hallucinate or generate conversational advice instead of concrete brand names. The Geo-Gap normalization pipeline filters out non-entities, conversational preamble, and generic phrases.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Provider</th>
                  <th className="py-3 px-4">Prompt ID</th>
                  <th className="py-3 px-4">Rejected Raw String (Noise / Hallucination)</th>
                  <th className="py-3 px-4">Filter Method</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {rejectedEntities.map((item, index) => (
                  <tr key={index} className="hover:bg-slate-800/40">
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-800 text-slate-300">
                        {item.provider}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                      {item.prompt_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-rose-300">
                      &ldquo;{item.raw}&rdquo;
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                        {item.method || 'pattern_filter'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
