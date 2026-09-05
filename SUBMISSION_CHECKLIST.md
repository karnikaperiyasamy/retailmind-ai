# NexusTiQ24 Hackathon — Submission Checklist
**Project**: RetailMind AI  
**Track**: PS03 (Retail — Sales and Inventory Copilot)  
**Tagline**: *"Evidence-driven sales and inventory intelligence for retail managers."*

---

## 1. Hackathon Verification Checklist

- [x] **TRACK_ID=PS03 first line**: Line 1 of `README.md` is strictly `TRACK_ID=PS03`
- [x] **requirements.txt works**: Minimal, clean dependencies compatible with Python 3.11
- [x] **Single-command start**: `python app.py` starts the entire backend and frontend
- [x] **localhost:8000 works**: Application listens on `http://localhost:8000` (or `PORT` env var)
- [x] **No npm or build step**: Frontend HTML/CSS/JS served directly by Flask
- [x] **No second terminal or Docker requirement**: Self-contained Python process
- [x] **Gemini API key environment variable**: Configured via `GEMINI_API_KEY` (never committed)
- [x] **No secrets committed**: `.env` is ignored by `.gitignore`; `.env.example` provided
- [x] **Generated data committed**: `data/stores.csv`, `products.csv`, `sales.csv`, `inventory.csv` committed
- [x] **Precomputed embeddings committed**: `data/embeddings/embeddings.npy` and `metadata.json` committed
- [x] **Local vector retrieval**: Uses `gemini-embedding-001` with `numpy` cosine similarity (Zero hosted vector DBs)
- [x] **Separation of concerns**: Python deterministically calculates all numbers; Gemini only explains facts
- [x] **Zero hallucinated numbers**: Strict grounding prevents model from inventing metrics
- [x] **Normal demo scenario works**: "What is running out?" displays Product, Store, Current stock, Daily sales, Days remaining, Reorder level, Calculation, Recommendation, and Lineage
- [x] **Difficult demo scenario 1 works**: "Why did sales decrease?" distinguishes what data proves vs cannot prove
- [x] **Difficult demo scenario 2 works**: "What will our exact sales be six months from now?" refuses to guess distant future
- [x] **Real commit history**: Meaningful, incremental commit history reflecting genuine development progression
- [x] **Deployment configuration**: `render.yaml` and `Procfile` configured for Render Web Service
- [x] **Automated test suite**: 25 automated unit and REST endpoint tests passing via `python -m unittest tests/test_retailmind.py`
- [x] **Submission documentation complete**: `README.md`, `DEMO_SCRIPT.md`, `PITCH.md`, `EVALUATION_MAPPING.md`
- [ ] **GitHub repository URL**: [Insert your GitHub repo URL here]
- [ ] **Application deployed URL**: [Insert Render live URL here once pushed]
- [ ] **Demo video link**: [Insert 3-5 minute demo video URL here]
- [ ] **Devfolio submission**: Ready for submission on Devfolio portal

---

## 2. Key Demo Commands & Verification

### To Run Locally:
```bash
pip install -r requirements.txt
python app.py
```
Visit: `http://localhost:8000`

### To Run Test Suite:
```bash
python -m unittest tests/test_retailmind.py
```

### To Verify Endpoints:
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/dashboard
curl http://localhost:8000/api/attention
curl -X POST http://localhost:8000/api/copilot -H "Content-Type: application/json" -d "{\"question\": \"What is running out?\"}"
```
