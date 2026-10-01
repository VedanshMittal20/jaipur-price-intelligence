import React, { useEffect, useState } from 'react';
import { DealSummary } from '../types/api';
import { fetchDeals } from '../api/client';
import { formatINR, formatPPSF, formatNumber } from '../lib/format';
import { Tag, TrendingDown, Search, Sparkles, ArrowRight } from 'lucide-react';

interface DealFinderProps {
  onInspectDeal: (locality: string, area: number, bhk: number) => void;
}

export const DealFinder: React.FC<DealFinderProps> = ({ onInspectDeal }) => {
  const [deals, setDeals] = useState<DealSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [bhkFilter, setBhkFilter] = useState<number | 'all'>('all');
  const [minDiscount, setMinDiscount] = useState<number>(15);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'discount' | 'price' | 'ppsf'>('discount');

  useEffect(() => {
    fetchDeals(100)
      .then((data) => setDeals(data))
      .catch((err) => setError(err.message || 'Failed to fetch deals'))
      .finally(() => setLoading(false));
  }, []);

  const filteredDeals = deals
    .filter((d) => {
      const matchesBhk = bhkFilter === 'all' || d.bhk === bhkFilter;
      const matchesDiscount = Math.abs(d.discount_pct) >= minDiscount;
      const matchesSearch = d.locality.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesBhk && matchesDiscount && matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === 'discount') return a.discount_pct - b.discount_pct; // most negative first
      if (sortBy === 'price') return a.actual_price_inr - b.actual_price_inr;
      return a.actual_ppsf - b.actual_ppsf;
    });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-2 text-rose-600 font-bold text-xs uppercase tracking-wider mb-1">
          <Tag className="w-4 h-4" />
          <span>Algorithmic Value Arbitrage</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          Jaipur Underpriced Deal Finder
        </h1>
        <p className="mt-2 text-sm text-slate-600 max-w-3xl">
          Verified listings in the market currently priced at least 15% below algorithmic fair valuation.
          Ranked by discount percentage.
        </p>
      </div>

      {/* Filter and Control Bar */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm mb-8 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search by Locality */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Locality Search
            </label>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Filter by locality..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          {/* BHK Filter */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Configuration (BHK)
            </label>
            <div className="flex space-x-1">
              {(['all', 1, 2, 3, 4] as const).map((b) => (
                <button
                  key={b}
                  onClick={() => setBhkFilter(b)}
                  className={`flex-1 py-2 text-xs font-semibold rounded-xl border transition-all ${
                    bhkFilter === b
                      ? 'bg-slate-900 text-white border-slate-900'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {b === 'all' ? 'All' : `${b} BHK`}
                </button>
              ))}
            </div>
          </div>

          {/* Minimum Discount Slider */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Min Discount
              </label>
              <span className="text-xs font-bold text-rose-600 font-mono">≥ {minDiscount}%</span>
            </div>
            <input
              type="range"
              min="15"
              max="35"
              step="1"
              value={minDiscount}
              onChange={(e) => setMinDiscount(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-600"
            />
          </div>

          {/* Sort By */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Sort Listings
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="discount">Deepest Discount (%)</option>
              <option value="price">Lowest Total Price (INR)</option>
              <option value="ppsf">Lowest Rate (₹/sq ft)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results State */}
      {loading ? (
        <div className="py-20 text-center text-slate-500">
          <p className="text-sm font-medium">Scanning model deals repository...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-50 text-rose-700 text-sm">
          Failed to load deals: {error}
        </div>
      ) : filteredDeals.length === 0 ? (
        <div className="py-16 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 p-8">
          <p className="text-base font-semibold text-slate-700">No matching deals found</p>
          <p className="text-xs text-slate-500 mt-1">Try lowering the minimum discount threshold or broadening locality filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDeals.map((deal) => {
            const savingsInr = deal.predicted_price_inr - deal.actual_price_inr;

            return (
              <div
                key={deal.listing_id}
                className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Top Badges */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-lg">
                      {deal.bhk} BHK • {formatNumber(deal.area_sqft)} sq ft
                    </span>
                    <span className="text-xs font-extrabold text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-full flex items-center space-x-1">
                      <TrendingDown className="w-3.5 h-3.5" />
                      <span>{deal.discount_pct.toFixed(1)}%</span>
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-slate-900 tracking-tight mb-3">
                    {deal.locality}
                  </h3>

                  {/* Pricing Comparison */}
                  <div className="bg-slate-50 rounded-xl p-3.5 space-y-2 mb-4">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs text-slate-500">Asking Price:</span>
                      <span className="text-lg font-extrabold text-slate-900 font-mono">
                        {formatINR(deal.actual_price_inr, true)}
                      </span>
                    </div>

                    <div className="flex justify-between items-baseline text-xs">
                      <span className="text-slate-500">Algorithmic Fair Value:</span>
                      <span className="font-semibold text-slate-600 line-through font-mono">
                        {formatINR(deal.predicted_price_inr, true)}
                      </span>
                    </div>

                    <div className="pt-2 border-t border-slate-200 flex justify-between items-center text-xs">
                      <span className="font-semibold text-emerald-700">Estimated Undervaluation:</span>
                      <span className="font-bold text-emerald-700 font-mono">
                        Save ~{formatINR(savingsInr, true)}
                      </span>
                    </div>
                  </div>

                  {/* Rates */}
                  <div className="flex justify-between text-xs text-slate-500 mb-4 px-1">
                    <span>Rate: <strong className="text-slate-800">{formatPPSF(deal.actual_ppsf)}</strong></span>
                    <span>Fair: <strong className="text-slate-500">{formatPPSF(deal.predicted_ppsf)}</strong></span>
                  </div>
                </div>

                {/* Inspect Action */}
                <button
                  onClick={() => onInspectDeal(deal.locality, deal.area_sqft, deal.bhk)}
                  className="w-full flex items-center justify-center space-x-1.5 py-2.5 px-3 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
                >
                  <Sparkles className="w-3.5 h-3.5 text-brand-400" />
                  <span>Inspect in Property Checker</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
