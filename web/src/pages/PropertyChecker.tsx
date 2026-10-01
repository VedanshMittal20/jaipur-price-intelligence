import React, { useState, useEffect } from 'react';
import {
  Building,
  Loader2,
  Sparkles,
  MapPin,
} from 'lucide-react';
import {
  CounterfactualScenario,
  LocalitySummary,
  PricePredictionResponse,
  PropertyRequest,
} from '../types/api';
import { fetchCounterfactuals, fetchLocalities, predictPrice } from '../api/client';
import { formatINR, formatPPSF, formatNumber } from '../lib/format';
import { FactorChart } from '../components/FactorChart';

interface PropertyCheckerProps {
  initialLocality?: string;
  initialArea?: number;
  initialBhk?: number;
}

export const PropertyChecker: React.FC<PropertyCheckerProps> = ({
  initialLocality,
  initialArea,
  initialBhk,
}) => {
  const [localities, setLocalities] = useState<LocalitySummary[]>([]);
  const [loadingLocalities, setLoadingLocalities] = useState(true);

  // Form State
  const [formData, setFormData] = useState<PropertyRequest>({
    area_sqft: 1350,
    bhk: 3,
    bathrooms: 3,
    floor: 2,
    total_floors: 6,
    property_type: 'Apartment',
    furnishing: 'Semi-Furnished',
    possession_status: 'Ready to Move',
    posted_by: 'Owner',
    rera_flag: 1,
    locality: initialLocality || 'Mansarovar',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PricePredictionResponse | null>(null);
  const [counterfactuals, setCounterfactuals] = useState<CounterfactualScenario[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Fetch localities on mount
  useEffect(() => {
    fetchLocalities()
      .then((data) => {
        setLocalities(data);
        if (!formData.locality && data.length > 0) {
          setFormData((prev) => ({ ...prev, locality: data[0].name }));
        }
      })
      .catch((err) => {
        console.error('Failed to load localities', err);
      })
      .finally(() => setLoadingLocalities(false));
  }, []);

  // Update initial parameters if props change
  useEffect(() => {
    let updated = { ...formData };
    let hasChanges = false;
    if (initialLocality && initialLocality !== formData.locality) {
      updated.locality = initialLocality;
      hasChanges = true;
    }
    if (initialArea && initialArea !== formData.area_sqft) {
      updated.area_sqft = initialArea;
      hasChanges = true;
    }
    if (initialBhk && initialBhk !== formData.bhk) {
      updated.bhk = initialBhk;
      updated.bathrooms = initialBhk;
      hasChanges = true;
    }
    if (hasChanges) {
      setFormData(updated);
      handleValuation(updated);
    }
  }, [initialLocality, initialArea, initialBhk]);

  const handleValuation = async (dataToSubmit = formData) => {
    setLoading(true);
    setError(null);
    try {
      const pred = await predictPrice(dataToSubmit);
      setResult(pred);
      const cf = await fetchCounterfactuals(dataToSubmit).catch(() => null);
      if (cf) setCounterfactuals(cf.scenarios);
    } catch (err: any) {
      setError(err.message || 'Valuation failed. Check your inputs.');
    } finally {
      setLoading(false);
    }
  };

  const applyScenario = (cf: CounterfactualScenario) => {
    const updated = { ...formData };
    if (cf.scenario_id === 'furnishing_upgrade') updated.furnishing = 'Furnished';
    if (cf.scenario_id === 'add_bathroom') updated.bathrooms = (updated.bathrooms || updated.bhk) + 1;
    if (cf.scenario_id === 'expand_area') updated.area_sqft = updated.area_sqft + 200;
    if (cf.scenario_id === 'possession_ready') updated.possession_status = 'Ready to Move';
    if (cf.scenario_id === 'rera_sanction') updated.rera_flag = 1;
    if (cf.scenario_id === 'mid_floor') updated.floor = 3;

    setFormData(updated);
    handleValuation(updated);
  };

  // Initial prediction on load once localities are ready
  useEffect(() => {
    if (!result && !loadingLocalities) {
      handleValuation();
    }
  }, [loadingLocalities]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleValuation();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Intro Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          Jaipur Property Price Checker
        </h1>
        <p className="mt-2 text-base text-slate-600 max-w-3xl">
          Get algorithmic fair asking price valuations calibrated for Jaipur micro-markets, complete with
          exact factor breakdowns and 80% conformal confidence intervals.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Input Form Column (5 Cols) */}
        <div className="lg:col-span-5">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-5 flex items-center space-x-2">
              <Building className="w-5 h-5 text-brand-600" />
              <span>Property Specification</span>
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Locality */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Locality / Neighborhood
                </label>
                <div className="relative">
                  <select
                    value={formData.locality}
                    onChange={(e) => setFormData({ ...formData, locality: e.target.value })}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white"
                  >
                    {localities.map((loc) => (
                      <option key={loc.locality_id} value={loc.name}>
                        {loc.name} ({loc.listing_count} listings)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Area */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Super Built-up Area (sq ft)
                  </label>
                  <span className="text-xs font-bold text-brand-600 font-mono">
                    {formatNumber(formData.area_sqft)} sq ft
                  </span>
                </div>
                <input
                  type="number"
                  min="200"
                  max="15000"
                  step="50"
                  value={formData.area_sqft}
                  onChange={(e) => setFormData({ ...formData, area_sqft: Number(e.target.value) })}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white"
                />
                {/* Area Quick Buttons */}
                <div className="flex space-x-1.5 mt-2">
                  {[900, 1350, 1800, 2400].map((sqft) => (
                    <button
                      key={sqft}
                      type="button"
                      onClick={() => setFormData({ ...formData, area_sqft: sqft })}
                      className={`text-xs px-2.5 py-1 rounded-md border transition-all ${
                        formData.area_sqft === sqft
                          ? 'bg-brand-50 border-brand-300 text-brand-700 font-semibold'
                          : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {sqft} sqft
                    </button>
                  ))}
                </div>
              </div>

              {/* BHK & Bathrooms */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Bedrooms (BHK)
                  </label>
                  <select
                    value={formData.bhk}
                    onChange={(e) => {
                      const bhk = Number(e.target.value);
                      setFormData({ ...formData, bhk, bathrooms: bhk });
                    }}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {[1, 2, 3, 4, 5, 6].map((num) => (
                      <option key={num} value={num}>
                        {num} BHK
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Bathrooms
                  </label>
                  <select
                    value={formData.bathrooms}
                    onChange={(e) => setFormData({ ...formData, bathrooms: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {[1, 2, 3, 4, 5, 6].map((num) => (
                      <option key={num} value={num}>
                        {num} Baths
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Property Type & Furnishing */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Type
                  </label>
                  <select
                    value={formData.property_type}
                    onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="Apartment">Apartment</option>
                    <option value="Independent House">Independent House</option>
                    <option value="Villa">Villa</option>
                    <option value="Builder Floor">Builder Floor</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Furnishing
                  </label>
                  <select
                    value={formData.furnishing}
                    onChange={(e) => setFormData({ ...formData, furnishing: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="Unfurnished">Unfurnished</option>
                    <option value="Semi-Furnished">Semi-Furnished</option>
                    <option value="Furnished">Furnished</option>
                  </select>
                </div>
              </div>

              {/* Floor & Possession */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Floor Level
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="50"
                    value={formData.floor}
                    onChange={(e) => setFormData({ ...formData, floor: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Possession Status
                  </label>
                  <select
                    value={formData.possession_status}
                    onChange={(e) => setFormData({ ...formData, possession_status: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="Ready to Move">Ready to Move</option>
                    <option value="Under Construction">Under Construction</option>
                  </select>
                </div>
              </div>

              {/* RERA and Poster */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-100">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.rera_flag === 1}
                    onChange={(e) => setFormData({ ...formData, rera_flag: e.target.checked ? 1 : 0 })}
                    className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500 border-slate-300"
                  />
                  <span className="text-xs font-semibold text-slate-700">RERA Approved Project</span>
                </label>

                <div className="text-xs text-slate-500">
                  Posted by:{' '}
                  <span className="font-semibold text-slate-700">{formData.posted_by}</span>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full mt-4 flex items-center justify-center space-x-2 bg-gradient-to-r from-brand-600 to-sky-600 hover:from-brand-700 hover:to-sky-700 text-white font-bold py-3.5 px-4 rounded-xl shadow-md shadow-brand-500/25 transition-all disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Computing Fair Value...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    <span>Estimate Fair Asking Price</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Results & Explanation Column (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">
              <span className="font-bold">Error:</span> {error}
            </div>
          )}

          {result && (
            <>
              {/* Valuation Hero Card */}
              <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 -mt-6 -mr-6 w-36 h-36 rounded-full bg-brand-500/10 blur-2xl pointer-events-none" />

                <div className="flex items-center justify-between text-xs font-medium text-slate-300 uppercase tracking-wider mb-2">
                  <span className="flex items-center space-x-1.5">
                    <MapPin className="w-3.5 h-3.5 text-brand-400" />
                    <span>{result.locality}</span>
                  </span>
                  <span className="bg-slate-700/60 text-slate-200 px-2.5 py-1 rounded-full border border-slate-600 text-[11px]">
                    {result.coord_precision === 'exact' ? 'Exact Coordinate Precision' : 'Locality Centroid Model'}
                  </span>
                </div>

                <div className="mt-3">
                  <span className="text-xs text-slate-400">Estimated Fair Asking Price</span>
                  <div className="flex items-baseline space-x-3 mt-1">
                    <span className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white font-mono">
                      {formatINR(result.estimate_inr, true)}
                    </span>
                    <span className="text-lg font-semibold text-brand-400">
                      ({formatINR(result.estimate_inr)})
                    </span>
                  </div>
                </div>

                {/* Secondary stats row */}
                <div className="mt-6 pt-6 border-t border-slate-700/60 grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="text-slate-400 block mb-0.5">Fair Unit Rate</span>
                    <span className="font-bold text-slate-100 text-sm">{formatPPSF(result.estimate_ppsf)}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-0.5">Rajasthan DLC Floor</span>
                    <span className="font-bold text-slate-100 text-sm">
                      {result.dlc_rate_per_sqm
                        ? `₹${formatNumber(result.dlc_rate_per_sqm)}/sqm`
                        : 'Unmapped colony'}
                    </span>
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <span className="text-slate-400 block mb-0.5">Typical Baseline Price</span>
                    <span className="font-bold text-slate-100 text-sm font-mono">
                      {formatINR(result.typical_price_inr, true)}
                    </span>
                  </div>
                </div>

                {/* Calibrated Conformal Interval Banner */}
                <div className="mt-6 p-3.5 bg-slate-800/80 border border-slate-700 rounded-xl flex items-center justify-between text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">
                      Calibrated 80% Conformal Interval:
                    </span>
                    <span className="font-bold text-brand-300 font-mono text-sm">
                      {formatINR(result.interval_low_inr, true)} — {formatINR(result.interval_high_inr, true)}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 block text-[11px]">Unit Rate Band:</span>
                    <span className="font-mono text-slate-200">
                      {formatPPSF(result.interval_low_ppsf)} - {formatPPSF(result.interval_high_ppsf)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Exact TreeSHAP Multiplicative Factor Decomposition */}
              <FactorChart factors={result.factors} groups={result.groups} />

              {/* What-If Counterfactual Value Simulator */}
              {counterfactuals.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-brand-600" />
                        <span>What-If Valuation Simulator</span>
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Simulate value changes under hypothetical upgrades or physical modifications
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    {counterfactuals.map((cf) => {
                      const isPos = cf.delta_inr >= 0;
                      return (
                        <div
                          key={cf.scenario_id}
                          className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-all flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-semibold text-xs text-slate-800">{cf.title}</span>
                              <span
                                className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
                                  isPos ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                                }`}
                              >
                                {isPos ? '+' : ''}{formatINR(cf.delta_inr, true)} ({cf.delta_pct >= 0 ? '+' : ''}{cf.delta_pct.toFixed(1)}%)
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-500 leading-tight mb-2.5">
                              {cf.description}
                            </p>
                          </div>

                          <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between">
                            <span className="text-[11px] text-slate-600 font-mono">
                              New: {formatINR(cf.new_estimate_inr, true)}
                            </span>
                            <button
                              type="button"
                              onClick={() => applyScenario(cf)}
                              className="text-[11px] font-bold text-brand-600 hover:text-brand-700 hover:underline"
                            >
                              Apply scenario &rarr;
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
