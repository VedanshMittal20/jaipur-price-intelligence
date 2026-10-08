import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { LocalityInsightResponse, LocalitySummary } from '../types/api';
import { fetchLocalities, fetchLocalityInsight } from '../api/client';
import { formatINR, formatPPSF, formatNumber } from '../lib/format';
import { MapPin, Search, ArrowRight, Sparkles } from 'lucide-react';

interface LocalityMapProps {
  onSelectLocality: (name: string) => void;
}

export const LocalityMap: React.FC<LocalityMapProps> = ({ onSelectLocality }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.CircleMarker[]>([]);

  const [localities, setLocalities] = useState<LocalitySummary[]>([]);
  const [selectedLocality, setSelectedLocality] = useState<LocalitySummary | null>(null);
  const [insight, setInsight] = useState<LocalityInsightResponse | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [tierFilter, setTierFilter] = useState<'all' | 'budget' | 'mid' | 'premium' | 'luxury'>('all');

  // Determine tier & color from PPSF
  const getTierInfo = (ppsf: number) => {
    if (ppsf < 3500) {
      return { tier: 'budget', label: 'Budget (< ₹3.5k)', color: '#10b981' };
    }
    if (ppsf < 5000) {
      return { tier: 'mid', label: 'Mid-Range (₹3.5k–5k)', color: '#0284c7' };
    }
    if (ppsf < 7000) {
      return { tier: 'premium', label: 'Premium (₹5k–7k)', color: '#f59e0b' };
    }
    return { tier: 'luxury', label: 'Luxury (> ₹7k)', color: '#8b5cf6' };
  };

  useEffect(() => {
    fetchLocalities()
      .then((data) => {
        setLocalities(data);
        if (data.length > 0) setSelectedLocality(data[0]);
      })
      .catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    if (!selectedLocality) {
      setInsight(null);
      return;
    }
    setInsightLoading(true);
    fetchLocalityInsight(selectedLocality.locality_id)
      .then((data) => setInsight(data))
      .catch((err) => {
        console.error('Failed to fetch locality insight:', err);
        setInsight(null);
      })
      .finally(() => setInsightLoading(false));
  }, [selectedLocality]);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current).setView([26.9124, 75.7873], 12);

    const streetLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
      {
        maxZoom: 18,
        attribution:
          'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, DeLorme, NAVTEQ, TomTom',
      }
    );

    const satelliteLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {
        maxZoom: 18,
        attribution:
          'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
      }
    );

    streetLayer.addTo(map);

    L.control.layers({
      'Default': streetLayer,
      'Satellite': satelliteLayer
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Render Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    const filtered = localities.filter((loc) => {
      const matchesSearch = loc.name.toLowerCase().includes(searchQuery.toLowerCase());
      const tier = getTierInfo(loc.median_ppsf).tier;
      const matchesTier = tierFilter === 'all' || tier === tierFilter;
      return matchesSearch && matchesTier;
    });

    filtered.forEach((loc) => {
      const { color } = getTierInfo(loc.median_ppsf);
      const radius = Math.min(22, Math.max(8, Math.sqrt(loc.listing_count) * 2.5));

      const marker = L.circleMarker([loc.lat, loc.lon], {
        radius,
        fillColor: color,
        fillOpacity: 0.75,
        color: '#ffffff',
        weight: 2,
      }).addTo(map);

      marker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 13px; line-height: 1.4;">
          <h4 style="font-weight: 700; margin: 0 0 4px; font-size: 14px; color: #0f172a;">${loc.name}</h4>
          <p style="margin: 0; color: #64748b; font-size: 11px;">${loc.listing_count} Listings Analyzed</p>
          <hr style="margin: 8px 0; border: none; border-top: 1px solid #e2e8f0;" />
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #64748b;">Median Price:</span>
            <strong style="color: #0f172a;">${formatINR(loc.median_price_inr, true)}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #64748b;">Median Rate:</span>
            <strong style="color: #0284c7;">${formatPPSF(loc.median_ppsf)}</strong>
          </div>
          ${
            loc.dlc_rate_per_sqm
              ? `<div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                   <span style="color: #64748b;">DLC Circle Rate:</span>
                   <strong style="color: #10b981;">₹${formatNumber(loc.dlc_rate_per_sqm)}/m²</strong>
                 </div>`
              : ''
          }
        </div>
      `);

      marker.on('click', () => {
        setSelectedLocality(loc);
      });

      markersRef.current.push(marker);
    });
  }, [localities, searchQuery, tierFilter]);

  const handleLocalityCardClick = (loc: LocalitySummary) => {
    setSelectedLocality(loc);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([loc.lat, loc.lon], 14, { duration: 1.2 });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Title */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Jaipur Locality Intelligence Map</h1>
          <p className="mt-1 text-sm text-slate-600">
            Geospatial price benchmarks, statutory DLC circle rates, and micro-market profiles.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs bg-white border border-slate-200 p-2.5 rounded-xl shadow-sm">
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
            <span className="text-slate-600">Budget (&lt;3.5k)</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-sky-600 inline-block" />
            <span className="text-slate-600">Mid-Range (3.5k–5k)</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" />
            <span className="text-slate-600">Premium (5k–7k)</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-purple-600 inline-block" />
            <span className="text-slate-600">Luxury (&gt;7k)</span>
          </span>
        </div>
      </div>

      {/* Main Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sidebar Localities List (4 Cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Search and Filter */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search Jaipur localities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex flex-wrap gap-1.5">
              {(['all', 'budget', 'mid', 'premium', 'luxury'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTierFilter(t)}
                  className={`text-xs px-2.5 py-1 rounded-md capitalize font-medium transition-all ${
                    tierFilter === t
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Selected Locality Detail Card */}
          {selectedLocality && (
            <div className="bg-gradient-to-br from-brand-900 to-slate-900 text-white p-5 rounded-2xl shadow-md space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase tracking-wider text-brand-300 font-semibold flex items-center space-x-1">
                  <MapPin className="w-3.5 h-3.5 text-brand-400" />
                  <span>Selected Micro-Market</span>
                </span>
                <span className="text-xs bg-brand-800/80 px-2 py-0.5 rounded-full border border-brand-700">
                  {selectedLocality.listing_count} Listings
                </span>
              </div>

              <h3 className="text-2xl font-bold tracking-tight">{selectedLocality.name}</h3>

              <div className="grid grid-cols-2 gap-3 pt-2 text-xs border-t border-brand-800/60">
                <div>
                  <span className="text-slate-400 block">Median Asking Price:</span>
                  <span className="text-base font-bold text-white font-mono">
                    {formatINR(selectedLocality.median_price_inr, true)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Median Unit Rate:</span>
                  <span className="text-base font-bold text-brand-300 font-mono">
                    {formatPPSF(selectedLocality.median_ppsf)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Statutory DLC Rate:</span>
                  <span className="text-xs font-semibold text-emerald-400">
                    {selectedLocality.dlc_rate_per_sqm
                      ? `₹${formatNumber(selectedLocality.dlc_rate_per_sqm)}/m²`
                      : 'Standard zone'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Metro Corridor:</span>
                  <span className="text-xs font-semibold text-sky-300">
                    {selectedLocality.dist_metro_km
                      ? `${selectedLocality.dist_metro_km.toFixed(1)} km to station`
                      : 'Feeder bus zone'}
                  </span>
                </div>
              </div>

              {/* Grounded Autonomous Insights */}
              {insightLoading && (
                <div className="py-2 text-center text-xs text-brand-300 animate-pulse">
                  Computing grounded micro-market intelligence...
                </div>
              )}

              {insight && !insightLoading && (
                <div className="pt-3 border-t border-brand-800/70 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center space-x-1 text-amber-300 font-semibold">
                      <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                      <span>Grounded Intelligence</span>
                    </span>
                    {insight.market_to_dlc_ratio && (
                      <span className="bg-brand-800/90 text-amber-200 text-[11px] px-2 py-0.5 rounded-full font-mono border border-brand-700/60">
                        {insight.market_to_dlc_ratio.toFixed(2)}x DLC Circle Rate
                      </span>
                    )}
                  </div>

                  <p className="text-slate-300 text-xs leading-relaxed font-sans">
                    {insight.narrative}
                  </p>

                  {insight.key_drivers.length > 0 && (
                    <div className="pt-1 space-y-1">
                      <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                        Key Price Drivers
                      </div>
                      <ul className="space-y-1">
                        {insight.key_drivers.map((driver, idx) => (
                          <li key={idx} className="flex items-start space-x-1.5 text-slate-300 text-xs">
                            <span className="text-emerald-400 font-bold">•</span>
                            <span>{driver}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <button
                onClick={() => onSelectLocality(selectedLocality.name)}
                className="w-full mt-2 flex items-center justify-center space-x-1.5 bg-brand-500 hover:bg-brand-600 text-white font-bold py-2.5 px-3 rounded-xl text-xs transition-all shadow-sm"
              >
                <span>Value a property in {selectedLocality.name}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Localities Scroll Area */}
          <div className="max-h-[300px] overflow-y-auto space-y-2 pr-1">
            {localities
              .filter((loc) => loc.name.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((loc) => {
                const isSelected = selectedLocality?.locality_id === loc.locality_id;
                const { color } = getTierInfo(loc.median_ppsf);

                return (
                  <div
                    key={loc.locality_id}
                    onClick={() => handleLocalityCardClick(loc)}
                    className={`p-3 rounded-xl border text-sm cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-brand-50/70 border-brand-300 shadow-sm'
                        : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                        <span className="font-semibold text-slate-800">{loc.name}</span>
                      </div>
                      <span className="text-xs font-mono font-bold text-slate-700">
                        {formatPPSF(loc.median_ppsf)}
                      </span>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Leaflet Map Column (8 Cols) */}
        <div className="lg:col-span-8">
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm h-[640px] relative">
            <div ref={mapContainerRef} className="w-full h-full z-0" />
          </div>
        </div>
      </div>
    </div>
  );
};
