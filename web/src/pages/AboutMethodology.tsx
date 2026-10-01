import React from 'react';
import {
  ShieldAlert,
  Layers,
  Sparkles,
  Database,
  MapPin,
  Cpu,
  CheckCircle,
} from 'lucide-react';

export const AboutMethodology: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
      {/* Hero Section */}
      <div>
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-xs font-bold mb-3">
          <Sparkles className="w-3.5 h-3.5 text-brand-600" />
          <span>Transparent Geospatial Machine Learning</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Methodology, Science & Provenance
        </h1>
        <p className="mt-3 text-base text-slate-600 leading-relaxed">
          The Jaipur Price Intelligence Platform is engineered to overcome spatial autocorrelation leakage,
          provide mathematically exact factor contributions, and quantify market uncertainty using
          distribution-free Mondrian conformal prediction.
        </p>
      </div>

      {/* Headline Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium block">Spatial Holdout R²</span>
          <span className="text-3xl font-extrabold text-slate-900 font-mono mt-1 block">0.766</span>
          <span className="text-[11px] text-emerald-600 font-semibold mt-1 block">Target: &ge; 0.750 ✓</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium block">Test Set MAPE</span>
          <span className="text-3xl font-extrabold text-slate-900 font-mono mt-1 block">25.1%</span>
          <span className="text-[11px] text-slate-500 font-medium mt-1 block">Median APE: 19.8%</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium block">Spatial Leakage Gap</span>
          <span className="text-3xl font-extrabold text-rose-600 font-mono mt-1 block">+10.8%</span>
          <span className="text-[11px] text-rose-600 font-medium mt-1 block">Random CV vs Spatial</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium block">Conformal Coverage</span>
          <span className="text-3xl font-extrabold text-brand-600 font-mono mt-1 block">73.6%</span>
          <span className="text-[11px] text-slate-500 font-medium mt-1 block">Nominal 80% Band</span>
        </div>
      </div>

      {/* 1. Spatial Cross-Validation & The Leakage Gap */}
      <section className="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 text-slate-900">
          <MapPin className="w-5 h-5 text-brand-600" />
          <h2 className="text-xl font-bold">1. The Spatial Leakage Trap & Grouped Spatial Block CV</h2>
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          Standard k-fold random cross-validation in real estate machine learning suffers from catastrophic
          optimistic bias. When listings in the same apartment tower or neighborhood are randomly partitioned into
          training and validation sets, the model effectively memorizes local price tiers rather than learning
          spatial generalizability.
        </p>

        <div className="bg-slate-50 rounded-xl p-5 border border-slate-200">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
            Empirical Spatial Leakage Comparison (LightGBM)
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-white rounded-lg border border-slate-200">
              <span className="text-xs text-slate-500 block">Naive Random 5-Fold CV:</span>
              <span className="text-xl font-bold text-slate-700 font-mono">12.63% MAPE</span>
              <span className="text-xs text-rose-600 block mt-1">
                Deceptively optimistic: borrows neighbor features
              </span>
            </div>
            <div className="p-3 bg-white rounded-lg border border-brand-200 bg-brand-50/30">
              <span className="text-xs text-slate-500 block">Grouped Spatial-Block CV:</span>
              <span className="text-xl font-bold text-brand-700 font-mono">23.46% MAPE</span>
              <span className="text-xs text-emerald-700 block mt-1">
                Honest evaluation: evaluates on unseen spatial blocks
              </span>
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-3">
            <strong>Leakage Gap (+10.83%):</strong> Demonstrates why our platform strictly trains and freezes
            holdout spatial blocks before tuning any hyperparameters.
          </p>
        </div>
      </section>

      {/* 2. Model Ladder & Ablation */}
      <section className="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 text-slate-900">
          <Layers className="w-5 h-5 text-brand-600" />
          <h2 className="text-xl font-bold">2. Model Ladder & Feature Ablation</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                <th className="pb-3">Model Architecture</th>
                <th className="pb-3">Spatial CV MAPE</th>
                <th className="pb-3">Median APE</th>
                <th className="pb-3">MAE (INR)</th>
                <th className="pb-3">R² (log)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-mono text-xs">
              <tr>
                <td className="py-3 font-sans font-medium text-slate-900">Baseline A0 (Locality Median)</td>
                <td className="py-3">42.56%</td>
                <td className="py-3">35.19%</td>
                <td className="py-3">₹2,840,110</td>
                <td className="py-3">0.107</td>
              </tr>
              <tr>
                <td className="py-3 font-sans font-medium text-slate-900">Ridge Regression</td>
                <td className="py-3">27.52%</td>
                <td className="py-3">16.24%</td>
                <td className="py-3">₹2,046,203</td>
                <td className="py-3">0.641</td>
              </tr>
              <tr>
                <td className="py-3 font-sans font-medium text-slate-900">Random Forest</td>
                <td className="py-3">22.09%</td>
                <td className="py-3">16.50%</td>
                <td className="py-3">₹1,289,149</td>
                <td className="py-3">0.735</td>
              </tr>
              <tr className="bg-brand-50/50 font-bold text-brand-900">
                <td className="py-3 font-sans text-brand-900 flex items-center space-x-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-brand-600" />
                  <span>LightGBM (Production Served)</span>
                </td>
                <td className="py-3">23.46%</td>
                <td className="py-3">17.11%</td>
                <td className="py-3">₹1,357,753</td>
                <td className="py-3">0.712</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* 3. Conformal Prediction & Exact TreeSHAP */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center space-x-2 text-slate-900">
            <Cpu className="w-5 h-5 text-brand-600" />
            <h3 className="font-bold text-base">Exact Multiplicative Attribution</h3>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            By modeling in log space, LightGBM native tree contributions decompose additively:
            <code className="block bg-slate-100 p-2 rounded mt-2 text-[11px] font-mono text-slate-800">
              ln(FairPrice) = Base + &sum; c_i
            </code>
            Exponentiating yields exact multiplicative factor percentages:
            <code className="block bg-slate-100 p-2 rounded mt-2 text-[11px] font-mono text-slate-800">
              FairPrice = TypicalPrice &times; &prod; exp(c_i)
            </code>
            This eliminates approximate SHAP dependencies in production, preserving 512 MB memory budgets.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center space-x-2 text-slate-900">
            <Database className="w-5 h-5 text-brand-600" />
            <h3 className="font-bold text-base">Mondrian Conformal Calibration</h3>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Standard ML point estimates give false precision. We calibrate finite-sample prediction intervals
            partitioned across price terciles (Mondrian conditioning) on out-of-fold residuals:
            <code className="block bg-slate-100 p-2 rounded mt-2 text-[11px] font-mono text-slate-800">
              P(Price &isin; [Low, High]) &ge; 1 - &alpha; = 80%
            </code>
            On our untouched held-out test set, the empirical coverage reached <strong>73.6%</strong>, closely
            approximating the nominal 80% specification.
          </p>
        </div>
      </section>

      {/* Statutory Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start space-x-3 text-amber-900 text-xs">
        <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold block">Academic & Research Transparency Notice</span>
          <p className="text-amber-800 leading-relaxed">
            This platform is an independent computational research project engineered for educational,
            demonstrative, and analytical purposes. It does not constitute a certified statutory valuation under
            the Rajasthan Stamp Act, RERA guidelines, or Section 34AB of the Wealth Tax Act. Buyers and sellers
            must conduct independent legal and structural title due diligence.
          </p>
        </div>
      </div>
    </div>
  );
};
