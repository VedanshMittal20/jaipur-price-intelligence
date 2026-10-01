# Data Sources and Licensing Audit

**Audit Date:** 2026-09-30  
**Auditor:** Executor  
**Applicable Rules:** Execution Plan Part B7 (Data legality and ethics), ADR-10  

---

## 1. Candidate Sources Evaluation & Audit Table

| ID | Source Name | Author / Organization | URL | Exact Licence Text / Terms | Row Count & Scope | Collection Method | Known Biases & Quality Issues | Verdict | Publishing Consequence |
|---|---|---|---|---|---|---|---|---|---|
| **SRC-1** | Real Estate Property Dataset | Karan Veer (`karanveer59`) | [Kaggle Dataset](https://www.kaggle.com/datasets/karanveer59/real-estate-property-dataset) | `Attribution 4.0 International (CC BY 4.0)` | ~10k–15k rows; Jaipur, Rajasthan (`flats_dataset.csv`, 1.63 MB) | Cleaned listings from property aggregators | Asking prices (not registry prices); residential flats focus; curated for educational use | `ALLOWED` | Commit derived artifacts, model, and download script `scripts/download_karanveer_jaipur.py`. Raw file can be downloaded or versioned with attribution. |
| **SRC-2** | House Price Prediction Challenge | Anmol Kumar / Devrup Banerjee (MachineHack) | [Kaggle Dataset](https://www.kaggle.com/datasets/anmolkumar/house-price-prediction-challenge) | `GPL 2` (GNU General Public License v2.0) | 29,451 (Train) + 68,720 (Test); Pan-India | Aggregated from property portals across India | Mixed cities; addresses need string parsing for Jaipur; coordinate accuracy varies; price in Lakhs | `ALLOWED` | Ship download script `scripts/download_anmolkumar.py`. Filter Jaipur rows at ingest. |
| **SRC-3** | Housing Prices in Metropolitan Areas of India | Ruchi Bhatia (`ruchi798`) | [Kaggle Dataset](https://www.kaggle.com/datasets/ruchi798/housing-prices-in-metropolitan-areas-of-india) | `CC0: Public Domain` | 28,979 listings across 6 Tier-1 metros | Scraped property listings | Does not contain Jaipur listings; amenity value `9` represents "not stated" | `ALLOWED` (Benchmarking only) | Do NOT mix into Jaipur training dataset. Keep for pipeline prototyping if needed. |
| **SRC-4** | OpenStreetMap (OSM) Jaipur Extract | OpenStreetMap contributors | [OpenStreetMap](https://www.openstreetmap.org/) / Overpass API / Geofabrik | `Open Database License (ODbL) 1.0` ("© OpenStreetMap contributors") | Spatial nodes/ways in bbox `(26.75, 75.65, 27.05, 76.00)` | Collaborative geospatial survey | Outskirts have fewer amenity tags than city center; road lines require metric projection and densification | `ALLOWED` | Ship extraction script `src/jpi/geo/osm_build.py` + derived `artifacts/geo/geo_layers.npz`. Mandatory attribution in README and UI footer. |
| **SRC-5** | Rajasthan DLC Rates (District Level Committee) | Government of Rajasthan (Registration & Stamps Dept / e-Panjiyan) | [e-Panjiyan Portal](https://epanjiyan.rajasthan.gov.in/) | Official State Public Gazette / Government Valuation Schedule | Residential circle rates across Jaipur urban colonies | Manual lookup of published circle rates (strictly no captcha bypass) | Administrative floor rates, not market transactions; colony names differ from portal commercial names | `ALLOWED` | Commit manual curated table `data/external/dlc_rates.csv` with source URLs and gazette dates. |
| **SRC-6** | Agency Real Estate Client Data (HabiGo 360) | Owner / HabiGo 360 Clients | Private Agency Records | Proprietary / Client Confidential | Private listings and inquiries in Jaipur micro-markets | Direct client transactions and inquiries | Highly localized; potential selection bias towards client inventory | `RESTRICTED` | Do NOT commit or redistribute raw data. Use only with written Owner approval (H1/H6) for validation/case study. |
| **SRC-7** | Manual Public Listing Sample | Project Owner / Executor | Public listing inspection | Personal research / fair dealing | 30–50 listings across major Jaipur localities | Hand-recorded verification sample | Small sample size; human recording errors possible | `RESTRICTED` | Private analysis and test set error inspection only. Do not redistribute raw listings. |
| **SRC-8** | Automated Web Scraping of Commercial Property Portals | Commercial Portals (99acres, Magicbricks, Housing.com) | Commercial URLs | Prohibited by Terms of Service & `robots.txt` (`Disallow: /`) | N/A | Automated web scraping | Legal and ToS violation; anti-scraping blocks | `PROHIBITED` | Strictly zero scraping permitted. Do not build or run scrapers against commercial property portals. |

---

## 2. Verdict Definitions & Operating Rules

1. **`ALLOWED`**: Source terms explicitly permit use, adaptation, and sharing. Raw or derived artifacts can be used according to specified attribution.
2. **`RESTRICTED`**: Data may only be used for private, offline verification or internal testing. No raw records published in public git commits.
3. **`PROHIBITED`**: ToS or `robots.txt` forbids automated ingestion or scraping. No data from these sources may enter the repository.
4. **`UNKNOWN`**: Must not be used until reviewed and approved by the Owner.

---

## 3. Mandatory Attribution Notices

- **OpenStreetMap**: `"© OpenStreetMap contributors"` (ODbL 1.0). Must appear in:
  - Project `README.md`
  - Application footer (`web/src/components/Footer.tsx`)
  - Methodology page (`web/src/pages/About.tsx`)
- **Kaggle Datasets**: Attribution to authors (`karanveer59`, `anmolkumar`) included in `DATA_CARD.md` and `README.md`.
- **Government of Rajasthan**: Notified DLC circular citations included in `DATA_CARD.md`.
