import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { PropertyChecker } from './pages/PropertyChecker';
import { LocalityMap } from './pages/LocalityMap';
import { DealFinder } from './pages/DealFinder';
import { AboutMethodology } from './pages/AboutMethodology';

export function App() {
  const [activeTab, setActiveTab] = useState<'checker' | 'map' | 'deals' | 'methodology'>('checker');
  const [selectedLocality, setSelectedLocality] = useState<string>('Mansarovar');
  const [dealParams, setDealParams] = useState<{ area?: number; bhk?: number }>({});

  const handleSelectLocalityFromMap = (localityName: string) => {
    setSelectedLocality(localityName);
    setActiveTab('checker');
  };

  const handleInspectDeal = (locality: string, area: number, bhk: number) => {
    setSelectedLocality(locality);
    setDealParams({ area, bhk });
    setActiveTab('checker');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between selection:bg-brand-500 selection:text-white">
      <div>
        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

        <main className="animate-in fade-in duration-300">
          {activeTab === 'checker' && (
            <PropertyChecker
              initialLocality={selectedLocality}
              initialArea={dealParams.area}
              initialBhk={dealParams.bhk}
            />
          )}
          {activeTab === 'map' && <LocalityMap onSelectLocality={handleSelectLocalityFromMap} />}
          {activeTab === 'deals' && <DealFinder onInspectDeal={handleInspectDeal} />}
          {activeTab === 'methodology' && <AboutMethodology />}
        </main>
      </div>

      {/* Global Footer */}
      <footer className="mt-16 bg-white border-t border-slate-200 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <div>
            <span className="font-semibold text-slate-700">Jaipur Real Estate Price Intelligence Platform</span>
            <p className="mt-0.5">Engineered with LightGBM, Mondrian Conformal Prediction & OpenStreetMap</p>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-[11px]">
            <span>Data: CC BY 4.0 & GPL 2</span>
            <span>Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" className="underline hover:text-slate-800">OpenStreetMap contributors</a></span>
            <span>Statutory rates: Rajasthan e-Panjiyan</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
