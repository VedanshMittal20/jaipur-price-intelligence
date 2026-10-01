# Jaipur Real Estate Price Intelligence Platform — Execution Plan (v2)

**Audience:** any human or AI agent executing this project end to end, including one that starts with zero context.
**Owner:** Vedansh (B.E. CSE, Data Science) — portfolio project for Full-Stack, Data Science, and IT Consulting roles.
**Plan date:** 30 Sep 2026. Anything marked **[VERIFY]** depends on the outside world and must be re-checked live before you rely on it.
**Estimated effort:** ~225 hours of task time for the MVP plus ~30 hours of optional/stretch work (per-task estimates below, summed in Part F). Calendar time depends on who executes: an AI agent doing the implementation with the Owner reviewing at each gate fits ~6–8 weeks; a solo human at 10–15 h/week needs roughly 4–5 months for the MVP. Apply the cut order (Part F) if time is short.

---

## Part A — Read This First

### A1. How to use this document
1. Work through the phases **in order**. Every phase is a list of **task cards**. Every task card has an ID (e.g. `F4`), an estimate, dependencies, exact outputs, and a "Done when" test.
2. A phase ends with a **Gate** (G0–G7, see Part D — Gate checklists). Do not start the next phase until the gate passes or the human explicitly waives it.
3. Keep three living files current as you go (templates in Part E): `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/RESULTS.md`. Any agent that picks up the project cold must be able to resume from `PROGRESS.md` alone.
4. **Never invent facts, data, or numbers.** Every number in the README, blog post, or resume text must come from `docs/RESULTS.md`, which is generated from real runs.
5. If you are blocked or a decision is above your authority, use the **Escalation protocol** (Part D). Do not improvise silently on legal, data-source, or scope questions.

### A2. Roles
| Role | Who | Authority |
|---|---|---|
| **Owner (human)** | Vedansh | Approves data sources, scope cuts, hosting spend, public claims (resume/blog), and anything involving other people's data |
| **Executor** | Any agent or person following this plan | Everything inside a task card; small engineering decisions (log in DECISIONS.md) |
| **Reviewer** | A second agent or the Owner | Runs the gate checklists; must not be the same context that wrote the work when possible |

### A3. Task card format
```
### ID — Title (est. Xh · needs: IDs)
Do:            numbered steps
Output:        exact files / artifacts produced
Done when:     objectively checkable condition(s)
Pitfalls:      known ways this goes wrong
```

### A4. Status vocabulary
`TODO` · `DOING` · `BLOCKED(reason)` · `DONE` · `WAIVED(by whom, why)`. Record in `docs/PROGRESS.md`.

### A5. What changed from v1
| v1 | v2 |
|---|---|
| Generic phases | Task cards with IDs, estimates, dependencies, outputs, and "Done when" tests |
| Generic hosting advice | Verified free-tier limits and a **lean-serving architecture** designed around them (Section B4) |
| "Find a dataset" | Concrete source shortlist, a coverage-audit procedure, and a numeric go/no-go decision table (Phase 0) |
| Approximate SHAP effects | **Exact multiplicative effects** using a natural-log target and LightGBM's native `pred_contrib` (no `shap` in the API image) |
| Interval coverage mentioned | Full conformal procedure using out-of-fold residuals, with a coverage test |
| Feature parity mentioned | One shared `NearestIndex` implementation and a parity test that fails CI |
| Text checklists | Working code scaffolds, Makefile, CI, Dockerfile, gate checklists, audits, agent prompts, templates |
| — | DLC (government circle-rate) prior as a legitimate external feature; optional client-validation track |
| Effort "5–6 weeks part-time" | **Corrected:** v1's estimate was optimistic for a solo human. v2 sums per-task estimates (~225 h MVP) and gives calendar scenarios |

---

## Part B — Project Definition, Research, Decisions

### B1. One-line pitch
A geospatial ML platform that estimates fair asking prices for Jaipur residential properties, explains *why* (exact per-factor effects), quantifies uncertainty with calibrated intervals, and flags listings priced unusually high or low relative to the model — on an interactive map.

### B2. Users and jobs-to-be-done
| User | Job | Feature |
|---|---|---|
| Home buyer | "Is this asking price reasonable, and why?" | Property Checker: estimate, 80% interval, factor breakdown |
| Broker / developer | "Which areas are pricey and what drives value?" | Locality map, drivers, benchmarking |
| Recruiter / interviewer | "Can this person ship a rigorous data product?" | Live demo, clean repo, model card, honest metrics, case study |

### B3. Scope
**MVP (must ship):**
- Cleaned Jaipur listing dataset from **legally usable** sources (target ≥ 3,000 rows; floor 1,500 — see the Phase 0 decision table).
- Geospatial features from OpenStreetMap (+ optional DLC circle-rate prior).
- Model ladder, spatial cross-validation, tuning, feature ablation, calibrated intervals, exact explanations.
- FastAPI backend + React/TypeScript/Leaflet frontend: Property Checker, Locality Map, Deal Finder, About/Methodology.
- Docker, CI, public deployment, README, model card, case study.

**Stretch (only after Gate G6):** locality trend view (needs dated data), what-if counterfactuals, drift monitor, MLflow model registry, client validation track, LLM "explain this locality" box grounded only on computed stats.

**Out of scope:** user accounts, payments, live scraping in production, commercial/land valuation, any claim to be a certified valuation.

### B4. Research findings (as of 30 Sep 2026) — the facts that shape this plan
Every item below was looked up when this plan was written. Re-verify anything that could have changed.

**1. Public listing datasets — availability and fit**
| Source | What it is | Fit for Jaipur | Action |
|---|---|---|---|
| Kaggle "House Price Prediction Challenge" (anmolkumar) | India-wide dataset described as collected across property aggregators, 12 predictor columns | Jaipur coverage **unknown** — must be counted (filter address text for "Jaipur") | Run coverage audit R3 |
| Kaggle "Housing Prices in Metropolitan Areas of India" (ruchi798) | Scraped new/resale listings for India's metropolitan areas, ~40 variables, amenity flags (a value of `9` means "not stated", not "absent") | Jaipur is probably **not** covered — **[VERIFY]** the city list | Use only if Jaipur present; otherwise optional pipeline-prototyping data, never mixed into Jaipur training |
| Owner's agency real-estate clients (HabiGo 360) | Listings/inquiries the clients own | Potentially the best data: local, fresh, real | Only with **written permission and anonymisation**; Owner decision H1 |
| Manually recorded sample | Individually viewed public listings recorded by hand | Small; useful to fill gaps and to sanity-check the model | Owner decision H1; personal-analysis use only, never redistributed |
| Web-scraping property portals | — | Portals commonly forbid it in their terms | **Do not scrape** unless ToS + robots.txt explicitly allow it (R2) |

**2. DLC circle rates (government minimum registration values)**
- Rajasthan publishes DLC rates by district → SRO → zone → colony via the state e-Panjiyan/IGRS portal.
- The lookup form uses a **captcha**. **Do not bypass captchas or automate around them.** Collect rates for a limited set of localities by hand (task D5), or use an official downloadable list if one exists **[VERIFY]**.
- Rates are revised periodically (a 10% increase for Jaipur from 1 Apr 2024 was reported; **[VERIFY]** the current schedule) and distinguish main-road vs interior categories.
- **Unit trap:** sources disagree on the unit (per sq ft vs per sq m). Confirm the unit from the portal itself before using.
- A DLC rate is a **legal floor, not a market price**. It is an *external* government-published number, not derived from the target, so it is a legitimate feature (`dlc_rate_per_sqm`, `dlc_category`), not leakage.

**3. Hosting reality (free tiers)**
| Host | Verified facts | Consequence |
|---|---|---|
| Render (free web service) | 512 MB RAM, 0.1 CPU; spins down after 15 min idle; ~30–60 s cold start; 750 free instance-hours/month. Free Postgres **expires** (recent sources say 30 days; older docs said 90) | The API image must stay **lean** and must **not depend on a free database** |
| Render (Starter, paid) | ~$7/month, 512 MB, 0.5 CPU, always on | Fallback if the free tier is unacceptable and the Owner approves spend |
| Hugging Face Spaces (Docker) | Docs list CPU Basic as 2 vCPU / 16 GB / free hardware; free Spaces sleep when unused. The same docs also state that Gradio/Docker (compute) Spaces require a paid plan while Static Spaces are free — **[VERIFY at signup]** | Best RAM headroom if the free path is actually open to you; otherwise use Render/Railway/Fly |
| Vercel / Netlify / Cloudflare Pages | Static frontend hosting | Host the React build here |

**4. OpenStreetMap and geocoding etiquette [VERIFY]:** OSM data is ODbL — attribution "© OpenStreetMap contributors" is mandatory. The public Nominatim instance limits usage to about 1 request/second, requires an identifying User-Agent, and expects caching; do not bulk-geocode against it. The public Overpass API is fair-use — cache everything.

### B5. Architecture decisions (pre-made; change only via DECISIONS.md)
| ID | Decision | Why |
|---|---|---|
| ADR-1 | **Static-artifact serving by default.** The deployed API loads model + `geo_layers.npz` + precomputed JSON/Parquet from disk. **No database in production.** | Free Postgres expires; a DB adds failure modes for zero demo value |
| ADR-2 | **PostGIS is optional, local-only** for analysis convenience. Everything the API needs is exported as files. | Keeps prod simple and free |
| ADR-3 | **Serving stack excludes geopandas, shapely, osmnx, shap, mlflow, matplotlib.** Allowed: numpy, pandas, scikit-learn (BallTree), lightgbm, fastapi, uvicorn, pydantic | Fits a 512 MB container; faster cold start |
| ADR-4 | **Distances use one shared class** (`NearestIndex`, haversine BallTree) for both training and serving. Roads are **densified to points every ≤ 50 m** at build time | Guarantees training/serving parity; max distance error ≈ 25 m |
| ADR-5 | **Target = natural log of price** (`np.log`, not `log1p`). Explanations = LightGBM `predict(pred_contrib=True)`; effects reported as exact multiplicative factors `exp(contribution)` | Additivity in log space makes the factor breakdown exact |
| ADR-6 | **Best model family expected: LightGBM** (verify in M3). If another family wins by a meaningful margin, keep LightGBM as the served model only if the loss is < 2% MAPE relative, otherwise update ADR-5's explanation method | Native contributions keep serving light |
| ADR-7 | **Model selection uses spatially grouped CV.** Random-split scores are reported only for comparison | Random splits leak neighbourhood information |
| ADR-8 | **Intervals via conformal calibration on out-of-fold residuals** (log scale), checked on the untouched test set | Distribution-free, simple, verifiable |
| ADR-9 | **Numbers ledger:** `docs/RESULTS.md` is generated by `make report`; docs quote from it only | Prevents stale/invented numbers |
| ADR-10 | **Raw third-party data is not committed** if its licence forbids redistribution; the repo ships download scripts + a data card instead | Legal safety |

### B6. Success metrics
| Metric | Target | Notes |
|---|---|---|
| MAPE, spatial-CV, held-out test | ≤ 20% (stretch ≤ 15%) | Report median APE too |
| R² on log-price, held-out test | ≥ 0.75 | |
| 80% interval empirical coverage | 75–85% | On the untouched test set |
| Spatial-CV vs random-split gap | Reported and explained | Shows leakage awareness |
| Geo-feature ablation lift | Reported (MAPE with vs without) | Key portfolio number |
| API `/predict` p95 latency (deployed, warm) | < 800 ms | |
| API RSS memory (measured in container) | < 400 MB | Leaves headroom on a 512 MB host |
| Backend test coverage | ≥ 70% | |
| Frontend Lighthouse (Perf / A11y / Best Practices) | ≥ 85 each | Document deviations |
| Reproducibility | Fresh clone → working app in ≤ 10 commands | |

**If targets are missed:** report the actual numbers honestly with the diagnosis. Honest and explained beats inflated.

### B7. Ground rules

**Data legality and ethics**
- Never scrape a site whose ToS or `robots.txt` prohibits it. Log the finding for every source in `docs/DATA_SOURCES.md`.
- Source preference order: (1) openly licensed datasets, (2) official published rate data, (3) OSM, (4) data the Owner/clients explicitly permit, (5) small manual samples for private analysis.
- Never store personal data: owner/agent names, phone numbers, emails, exact street addresses tied to individuals. Drop such columns at ingestion.
- **Never generate synthetic listings and present them as real data.** Synthetic data is allowed only for unit-test fixtures, clearly labelled.
- Attribute all sources (README + app footer). Show the disclaimer in the app: *"Estimates are statistical predictions for educational purposes, not a professional valuation."*
- Publishing policy: publish code, aggregates, derived model, data card, and download scripts. Publish raw rows only if the licence clearly allows it.

**Engineering**
- Python ≥ 3.11 and Node LTS **[VERIFY latest stable]**; pin all dependency versions; `SEED = 42` everywhere.
- No leakage: anything derived from the target is computed inside CV folds only.
- Notebooks explore; `src/` is the source of truth and is unit-tested. No notebook-only steps.
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), small PRs even when solo.
- No secrets in git. `.env.example` only.

### B8. Repository structure
```
jaipur-price-intelligence/
├── README.md  LICENSE  Makefile  docker-compose.yml  pyproject.toml  .env.example
├── .pre-commit-config.yaml   .github/workflows/ci.yml
├── docs/
│   ├── PROGRESS.md  DECISIONS.md  RESULTS.md        # living files (Part E templates)
│   ├── DATA_SOURCES.md  DATA_DICTIONARY.md  CLEANING_REPORT.md
│   ├── COVERAGE_REPORT.md  EDA_FINDINGS.md  ERROR_ANALYSIS.md
│   ├── MODEL_CARD.md  RESEARCH_NOTES.md  INTERVIEW_NOTES.md  DATA_CARD.md
│   ├── EXECUTION_PLAN.md  RUNBOOK.md  CHANGELOG.md  openapi.json
│   └── assets/                                        # figures, GIF, screenshots
├── data/
│   ├── raw/        # immutable; gitignored if licence forbids redistribution
│   ├── interim/  processed/
│   └── external/   # OSM extracts, DLC table, geocode cache, locality_map.csv
├── artifacts/                                          # everything the API loads
│   ├── model/      model.txt  preprocess.joblib  metadata.json  conformal.json
│   ├── geo/        geo_layers.npz  localities.geojson  locality_stats.json
│   └── scores/     listing_scores.parquet
├── scripts/        download_<source>.py                # reproducible public-data downloads
├── notebooks/      00_profile.ipynb  01_eda.ipynb  02_features.ipynb  03_modeling.ipynb
├── src/jpi/
│   ├── config.py
│   ├── data/       ingest.py  clean.py  validate.py  locality.py
│   ├── geo/        osm_build.py  nearest.py            # NearestIndex + GeoLayers live in nearest.py
│   ├── features/   build.py  transformers.py
│   ├── models/     cv.py  train.py  evaluate.py  conformal.py  explain.py
│   └── report.py   # generates docs/RESULTS.md
├── api/            main.py  schemas.py  deps.py  routers/  services/  tests/
├── web/            src/{components,pages,api,types,lib}  tests/
├── tests/          test_data.py  test_features.py  test_parity.py  test_model.py
└── mlruns/         # gitignored
```
