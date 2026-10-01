import React from 'react';
import { FeatureFactor, GroupFactor } from '../types/api';
import { formatPct } from '../lib/format';
import { TrendingUp, TrendingDown, Layers } from 'lucide-react';

interface FactorChartProps {
  factors: FeatureFactor[];
  groups: GroupFactor[];
}

export const FactorChart: React.FC<FactorChartProps> = ({ factors, groups }) => {
  const [viewMode, setViewMode] = React.useState<'features' | 'groups'>('features');

  const maxAbsEffect = Math.max(
    ...factors.map((f) => Math.abs(f.effect_pct)),
    ...groups.map((g) => Math.abs(g.effect_pct)),
    15
  );

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-base font-bold text-slate-900">Value Drivers & Factor Attribution</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Exact multiplicative decomposition relative to typical Jaipur property
          </p>
        </div>
        <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
          <button
            onClick={() => setViewMode('features')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              viewMode === 'features' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Key Factors
          </button>
          <button
            onClick={() => setViewMode('groups')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              viewMode === 'groups' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Group Categories
          </button>
        </div>
      </div>

      {viewMode === 'features' ? (
        <div className="space-y-3.5">
          {factors.map((f, i) => {
            const isPos = f.effect_pct >= 0;
            const barWidth = Math.min(100, (Math.abs(f.effect_pct) / maxAbsEffect) * 100);

            return (
              <div key={i} className="text-sm">
                <div className="flex justify-between items-center mb-1">
                  <div className="flex items-center space-x-1.5 font-medium text-slate-800">
                    {isPos ? (
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <TrendingDown className="w-3.5 h-3.5 text-rose-500" />
                    )}
                    <span>{f.label}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-slate-400 font-mono">({f.factor.toFixed(2)}x)</span>
                    <span
                      className={`text-xs font-bold font-mono px-1.5 py-0.5 rounded ${
                        isPos ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                      }`}
                    >
                      {formatPct(f.effect_pct)}
                    </span>
                  </div>
                </div>

                {/* Split Bar Visualization */}
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden flex relative">
                  <div className="w-1/2 flex justify-end">
                    {!isPos && (
                      <div
                        className="h-full bg-rose-400 rounded-l-full transition-all duration-500"
                        style={{ width: `${barWidth}%` }}
                      />
                    )}
                  </div>
                  <div className="w-0.5 h-full bg-slate-300 z-10" />
                  <div className="w-1/2 flex justify-start">
                    {isPos && (
                      <div
                        className="h-full bg-emerald-500 rounded-r-full transition-all duration-500"
                        style={{ width: `${barWidth}%` }}
                      />
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map((g, i) => {
            const isPos = g.effect_pct >= 0;
            const barWidth = Math.min(100, (Math.abs(g.effect_pct) / maxAbsEffect) * 100);

            return (
              <div key={i} className="text-sm">
                <div className="flex justify-between items-center mb-1">
                  <div className="flex items-center space-x-1.5 font-semibold text-slate-800">
                    <Layers className="w-4 h-4 text-brand-600" />
                    <span>{g.group}</span>
                  </div>
                  <span
                    className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${
                      isPos ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                    }`}
                  >
                    {formatPct(g.effect_pct)}
                  </span>
                </div>
                <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden flex relative">
                  <div className="w-1/2 flex justify-end">
                    {!isPos && (
                      <div
                        className="h-full bg-rose-400 rounded-l-full"
                        style={{ width: `${barWidth}%` }}
                      />
                    )}
                  </div>
                  <div className="w-0.5 h-full bg-slate-300 z-10" />
                  <div className="w-1/2 flex justify-start">
                    {isPos && (
                      <div
                        className="h-full bg-brand-500 rounded-r-full"
                        style={{ width: `${barWidth}%` }}
                      />
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center space-x-1">
          <span className="w-2 h-2 rounded-full bg-rose-400 inline-block"></span>
          <span>Discount / penalty factor</span>
        </span>
        <span className="flex items-center space-x-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
          <span>Premium / value add</span>
        </span>
      </div>
    </div>
  );
};
