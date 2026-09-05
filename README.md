TRACK_ID=PS03
# RetailMind AI
> Evidence-driven sales and inventory intelligence for retail managers.

RetailMind AI is an enterprise-grade retail sales and inventory intelligence copilot built for the **NexusTiQ24 Hackathon** under **Track PS03: Retail — Sales and Inventory Copilot**.

---

## 1. Problem Statement
A store manager's data is rich; their decisions are rushed. What needs attention today is buried across scattered daily sales reports, stock registers, and supplier sheets across multiple branch locations. 

When store managers attempt to use conventional conversational AI, they face critical business risks:
- **Hallucinated numbers**: General-purpose LLMs fabricate plausible-sounding inventory counts, stock days, and percentages.
- **Unsubstantiated claims**: AI diagnosing causes (e.g. blaming weather, competitors, or marketing) without actual transactional proof.
- **Premature autonomy**: Systems triggering unapproved orders or price changes without human-in-the-loop validation.

Store managers need plain-language answers backed by actual verified numbers, clear formula calculations, and explicit boundaries when the data cannot answer a question.

---

## 2. Solution: RetailMind AI
RetailMind AI bridges daily store transactions and stock registers with deterministic Python analytics and grounded Google Gemini GenAI reasoning.

- **Zero-Hallucination Architecture**: Python and pandas calculate all business metrics (inventory run rates, stock-out flags, overstock thresholds, sales surges, and declines).
- **Grounded Natural Language**: Gemini explains, contextualizes, and summarizes the verified evidence package without inventing a single metric.
- **Human-in-the-Loop Safeguards**: RetailMind AI recommends operational actions (DATA &rarr; CALCULATION &rarr; ASSUMPTION &rarr; RECOMMENDATION); store managers always make the final operational decision.
- **Honest Uncertainty Handling**: When data cannot prove the root cause of an anomaly or predict distant futures, the system explicitly states what the data proves versus what it cannot prove.

---

## 3. Core Features
1. **Executive SaaS Dashboard**:
   - High-level KPI cards: 30-Day Gross Revenue, Units Sold, Total Inventory Holding, Products at Risk, Overstocked SKUs, and Active Sales Alerts.
   - Interactive charts: 90-Day Gross Revenue Trendline, Sales by Category, Top 5 Products by Revenue, and Store Performance Share.
2. **Needs Attention Today (Attention Center)**:
   - Categorized alerts with priority weighting: Stock-Out Risk (&le; 7 days), Overstock (&ge; 45 days), Slow Moving (&le; 5 units sold in 60 days), Sales Spikes (+40%), and Sales Drops (-30%).
   - Structured 4-part evidence cards: **DATA**, **CALCULATION**, **ASSUMPTION**, and **RECOMMENDATION**.
3. **Ask RetailMind AI (AI Copilot)**:
   - Plain-language conversational assistant powered by Google Gemini and local semantic vector retrieval.
   - Traceable response structure: Answer, Supporting Evidence, Deterministic Calculations, Operational Recommendation, Assumptions, and Limitations.
   - Collapsible **"View Raw Evidence & Grounding Traceability"** drawer exposing underlying CSV lineage.
4. **Product Catalogue & Health Inspector**:
   - Filterable, searchable inventory directory across 32 SKUs in 6 categories.
   - Computed days of inventory, velocity run-rate, profit margins, and health status badges.
5. **Multi-Store Network Operations**:
   - Cross-store performance comparisons across Downtown Flagship (S001), Mall Store (S002), and Airport Express (S003).

---

## 4. System Architecture

```
User Question (Natural Language)
               │
               ▼
   [ Question Understanding ]
               │
               ▼
       [ Intent Routing ]
               │
               ├─────────────────────────────────────────┐
               ▼                                         ▼
   [ Local Semantic Retrieval ]           [ Deterministic Analytics Engine ]
 (gemini-embedding-001 + numpy)              (Python / pandas / math)
               │                                         │
               └────────────────────┬────────────────────┘
                                    │
                                    ▼
                         [ Evidence Package ]
            (Verified numbers, date ranges, calculations,
             stated assumptions, explicit limitations)
                                    │
                                    ▼
                     [ Grounded Google Gemini LLM ]
                                    │
                                    ▼
                   [ Structured Grounded Response ]
           (Answer + Evidence + Calculations + Recommendation
                   + Assumptions + Limitations)
```

---

## 5. Technology Stack
- **Backend**: Python 3.11, Flask 2.3+
- **Data & Analytics Engine**: pandas, numpy (vectorized time-series analysis)
- **GenAI Reasoning**: Google Gemini API (`gemini-1.5-flash` / `gemini-pro`) via `google-generativeai`
- **Vector Retrieval**: `gemini-embedding-001` with local `numpy` cosine similarity (Zero hosted vector DBs)
- **Frontend**: HTML5, CSS3 (Modern Dark Slate Enterprise theme), Vanilla JavaScript (ES6+), Chart.js (with pure SVG fallback)
- **Production Server**: Gunicorn WSGI server
- **Deployment Target**: Render Web Service (`render.yaml`, `Procfile`)

---

## 6. Retail Dataset
The application includes realistic synthetic retail data representing a 92-day continuous operational horizon (**June 1, 2026 to August 31, 2026**):
- **Stores (`data/stores.csv`)**:
  - `S001` — Downtown Store (Metro Central Hub)
  - `S002` — Mall Store (Westside Galleria)
  - `S003` — Airport Store (International Terminal 2 Departures)
- **Products (`data/products.csv`)**: 32 distinct SKUs spanning Electronics, Beverages, Grocery, Personal Care, Home, and Stationery.
- **Sales Transactions (`data/sales.csv`)**: 8,832 daily transaction records tracking units sold and gross revenue.
- **Inventory Snapshots (`data/inventory.csv`)**: 8,832 daily stock snapshots per product and store.

### Built-in Demo Scenarios:
1. **Critical Stock-Out Risk**: `P014` (Wireless Ergonomic Mouse) at `S002` (Mall Store) — current stock is 12 units with velocity of 2.43 units/day &rarr; 4.94 days of inventory remaining (below reorder point of 25 units).
2. **Severe Overstock**: `P008` (Organic Cold Brew 1L) at `S001` (Downtown Store) — stock stands at 420 units &rarr; 113.2 days of supply, locking up ₹49,440.00 in excess working capital.
3. **Sales Surge / Spike**: `P003` (Noise Cancelling Headphones) at `S001` — recent 7-day velocity spiked to 8.0 units/day vs 30-day baseline of 4.3 units/day (+59.9% surge).
4. **Sales Decline / Drop**: `P019` (Artisan Ceramic Mug) at `S002` — recent sales rate dropped from 3.8 to 1.4 units/day (-62.7% decline).
5. **Slow-Moving SKU**: `P027` (Premium Fountain Pen Set) at `S003` — only 1 unit sold in 60 days, holding 35 units in stock (₹33,250.00 locked capital).
6. **Healthy SKU**: `P005` (Whole Bean Dark Roast Coffee) — steady 18–22 days of inventory across branches.

---

## 7. Deterministic Analytics Logic
All business metrics are computed in `src/analytics.py` using defensive numeric operations:

### 1. Stock-Out Logic
$$\text{Average Daily Sales (7d)} = \frac{\sum_{t=-6}^{0} \text{Quantity Sold}_t}{7}$$
$$\text{Days of Inventory} = \frac{\text{Current Stock}}{\text{Average Daily Sales (7d)}}$$
- **Trigger**: Flagged when $\text{Days of Inventory} \le 7.0$ days.
- **Zero Division Defense**: If average daily sales equals 0, days of inventory is safely evaluated as $999.0$ (or $0.0$ if stock is zero).

### 2. Overstock Logic
$$\text{Target Stock} = \text{Average Daily Sales} \times 30 \text{ days}$$
$$\text{Excess Units} = \max(0, \text{Current Stock} - \text{Target Stock})$$
$$\text{Tied-Up Working Capital} = \text{Excess Units} \times \text{Cost Price}$$
- **Trigger**: Flagged when $\text{Days of Inventory} \ge 45.0$ days.

### 3. Sales Anomalies (Spikes & Drops)
$$\text{Percentage Change} = \frac{\text{Recent 7d Average} - \text{Baseline 30d Average}}{\text{Baseline 30d Average}} \times 100$$
- **Spike Trigger**: $\ge +40.0\%$
- **Drop Trigger**: $\le -30.0\%$

---

## 8. GenAI Integration & Grounding Strategy

### The Role of Google Gemini
Gemini is used exclusively for:
1. Natural language understanding and intent interpretation.
2. Synthesizing plain-language explanations of verified numerical facts.
3. Formulating contextualized operational suggestions for store managers.

Gemini is strictly forbidden from:
- Inventing missing transactional numbers or stock quantities.
- Guessing causal factors not tracked in the data.
- Fabricating distant forecasts.

### Gemini Embeddings & Local Retrieval
- Embedding Model: `gemini-embedding-001`
- Storage: Precomputed local index saved in `data/embeddings/embeddings.npy` and `data/embeddings/metadata.json` (committed to repository).
- Similarity Search: Local `numpy` dot-product cosine similarity. Zero external database overhead.
- Startup latency: Instantaneous (&le; 1 second).

### Graceful Fallback
If `GEMINI_API_KEY` is not provided or rate-limited:
- The entire application (Dashboard, Attention Center, Product Catalogue, Store Comparison) continues functioning at 100% capacity.
- The AI Copilot uses deterministic natural language synthesis and explicitly tags the response with `"engine": "Deterministic Analytics Engine (Gemini Offline)"`.

---

## 9. Handling Uncertainty & Difficult Demo Scenarios

### Difficult Scenario 1: Root Cause Speculation
- **User Question**: *"Why did sales decrease?"*
- **Application Response**: The copilot distinguishes **WHAT THE DATA PROVES** from **WHAT THE DATA CANNOT PROVE**:
  > *"The transaction records in sales.csv confirm that sales for Artisan Ceramic Mug 350ml at Mall Store decreased by 62.7% (from 3.8 to 1.4 units/day). However, the available dataset does not contain causal information (footfall counters, competitor promotions, pricing adjustments) to prove why this decline occurred."*

### Difficult Scenario 2: Distant Forecasting Speculation
- **User Question**: *"What will our exact sales be six months from now?"*
- **Application Response**: The copilot refuses to fabricate an unsupported prediction:
  > *"The current dataset does not contain sufficient historical depth or macroeconomic forecasting variables to reliably determine exact sales six months from now. Fabricating an exact numerical forecast without forward-looking contracts or seasonality models would be unsupported."*

---

## 10. Human-in-the-Loop Philosophy
Every recommendation generated by RetailMind AI includes an explicit safeguard:
```
DATA: Raw verified metrics from CSV
CALCULATION: Explicit mathematical formula
ASSUMPTION: Operational hypothesis
RECOMMENDATION: Action proposal for store manager
HUMAN SAFEGUARD: Manager evaluates local shelf conditions and supplier terms before placing orders.
```
RetailMind AI **recommends**; the human store manager **decides**. The system never triggers unapproved purchases, transfers, or pricing changes.

---

## 11. Installation & Running Locally

### Non-Negotiable Single-Command Execution
The application requires **zero npm builds**, **no docker**, and **no second terminal**.

```bash
# 1. Clone repository
git clone https://github.com/your-username/retailmind-ai.git
cd retailmind-ai

# 2. Install dependencies (Python 3.11 compatible)
pip install -r requirements.txt

# 3. Start application (Single Command)
python app.py
```

Open your browser and navigate to:
```
http://localhost:8000
```

### Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Inside `.env`:
```ini
# Optional: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Port configuration (defaults to 8000)
PORT=8000
```
*(Note: If `GEMINI_API_KEY` is omitted, the full dashboard and deterministic copilot remain 100% operational).*

---

## 12. REST API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the single-page application interface |
| `GET` | `/api/health` | Health check, dataset load counts, and Gemini status |
| `GET` | `/api/dashboard` | 30-day KPI cards, 90-day trendline, and category shares |
| `GET` | `/api/attention` | Prioritized operational alerts (stockout, overstock, spikes, drops) |
| `GET` | `/api/products` | Complete product catalogue with velocity and stock health |
| `GET` | `/api/stores` | Store performance breakdown and comparison benchmarks |
| `GET` | `/api/sales` | Historical sales trendline data |
| `GET` | `/api/inventory` | Aggregate inventory status summary |
| `POST` | `/api/copilot` | Natural-language query handler returning structured JSON |

---

## 13. Testing
Run the comprehensive automated test suite (25 test cases):
```bash
python -m unittest tests/test_retailmind.py
```

All tests execute in &le; 1 second, validating:
- Dataset integrity and schema conformity
- Deterministic math formulas and zero-division protection
- Local vector retrieval and cosine ranking
- Intent routing across all standard and edge cases
- Refusal of ungrounded causal speculation and distant forecasts
- Full REST API endpoint responses and HTTP status codes

---

## 14. Deployment Configuration
RetailMind AI is configured for one-click deployment to **Render**:
- `render.yaml`: Defines the web service, build command (`pip install -r requirements.txt`), and production start command (`gunicorn app:app`).
- `Procfile`: Standard `web: gunicorn app:app`.
- Binds to `0.0.0.0` and respects the `PORT` environment variable.

---

## 15. Repository Structure
```
retailmind-ai/
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore rules (secrets, pycache, env)
├── Procfile                  # Production process specification
├── render.yaml               # Render Web Service deployment configuration
├── requirements.txt          # Python dependencies (Python 3.11 compatible)
├── README.md                 # Primary documentation (First line TRACK_ID=PS03)
├── app.py                    # Single-command application entrypoint
│
├── data/                     # Synthetic retail datasets
│   ├── stores.csv            # 3 physical store locations
│   ├── products.csv          # 32 retail products across 6 categories
│   ├── sales.csv             # 92 days of transactional history (8,832 rows)
│   ├── inventory.csv         # 92 days of daily inventory snapshots (8,832 rows)
│   └── embeddings/           # Precomputed local vector store
│       ├── embeddings.npy    # Normalized vector embeddings
│       └── metadata.json     # Metadata index
│
├── src/                      # Core modular architecture
│   ├── __init__.py           # Package initialization
│   ├── data_loader.py        # Dataset caching, schema validation, and accessors
│   ├── data_generator.py     # Deterministic synthetic data generator
│   ├── analytics.py          # Pure Python deterministic analytics engine
│   ├── attention.py          # Prioritized alert aggregation service
│   ├── recommendations.py    # Grounded 4-part recommendation formulator
│   ├── retrieval.py          # Local semantic retrieval using numpy cosine similarity
│   ├── gemini_service.py     # Grounded Gemini LLM service with fallback
│   └── query_engine.py       # Intent router and evidence grounding orchestrator
│
├── templates/
│   └── index.html            # Responsive single-page dashboard UI
│
├── static/
│   ├── style.css             # Enterprise SaaS design system (Inter + Dark Slate)
│   └── app.js                # Frontend state management, charts, and copilot chat
│
└── tests/
    └── test_retailmind.py    # Automated test suite (25 unit and endpoint tests)
```

---

## 16. Demo Video
Demo Video:
[Add final demo video link here]

---

## 17. Limitations & Future Roadmap
- **Causal Data Boundaries**: Current transactional records track sales quantities and prices, but do not capture foot traffic counters, local weather patterns, or marketing ad spend.
- **Lead Time Homogeneity**: Reorder proposals currently assume a standard 3–5 day supplier lead time; integration with live EDI supplier feeds is planned for v2.0.
- **Physical Shelf Constraints**: Overstock excess calculations currently evaluate capital costs rather than volumetric cubic meter constraints.
