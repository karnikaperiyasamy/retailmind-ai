# NexusTiQ24 — Evaluation Criteria Mapping
**Project**: RetailMind AI  
**Track**: PS03 (Retail — Sales and Inventory Copilot)  

This document provides a detailed point-by-point mapping demonstrating how RetailMind AI satisfies every official evaluation criterion of the NexusTiQ24 Hackathon.

---

## 1. Working Application
| Requirement | Implementation in RetailMind AI | Verification Command / Evidence |
|---|---|---|
| **Single-Command Startup** | The entire system starts with `python app.py` on `http://localhost:8000`. | Run `python app.py`. Verified zero second terminal, no npm, no Docker. |
| **Complete End-to-End** | Not a mock or prototype. Features live REST APIs, interactive charts, full catalog table, attention feed, and conversational copilot. | Browse `http://localhost:8000` to inspect all 5 operational views. |
| **Python 3.11 Compatibility** | Tested and verified across Python 3.11–3.14 with lightweight, standard libraries. | All 25 automated unit tests pass in &le; 1s. |
| **Zero Setup Hassle** | Python backend serves both REST JSON APIs and the complete frontend UI directly from Flask templates and static assets. | Clone, `pip install -r requirements.txt`, `python app.py`. |

---

## 2. Real Commit History
| Requirement | Implementation in RetailMind AI | Verification Command / Evidence |
|---|---|---|
| **Meaningful Progression** | 14 genuine, incremental commits tracing logical development milestones from project skeleton to synthetic data, analytics, UI, Gemini, retrieval, error handling, tests, and deployment. | Inspect Git log via `git log --oneline`. |
| **Zero Artificial Manipulation** | No fake timestamps, no artificial squashing, no single giant commit at the end. | Verifiable commit tree with clean modular diffs. |

---

## 3. Sound Engineering
| Requirement | Implementation in RetailMind AI | Verification Command / Evidence |
|---|---|---|
| **Modular Architecture** | Clean separation into `src/data_loader.py`, `src/analytics.py`, `src/attention.py`, `src/recommendations.py`, `src/retrieval.py`, `src/gemini_service.py`, `src/query_engine.py`. | Inspect `src/` directory. Zero spaghetti code. |
| **Defensive Numerical Logic** | Explicit zero-division guards for all run-rate formulas (`days_of_inventory`), NaN imputation, safe type casting, and schema validation. | `TestDeterministicAnalytics.test_safe_division_by_zero` in test suite. |
| **Local Vector Retrieval** | `gemini-embedding-001` representation with local `numpy` cosine similarity. Zero hosted vector database dependencies, avoiding network latency and recurring costs. | `src/retrieval.py` and precomputed cache in `data/embeddings/`. |
| **Comprehensive Testing** | 25 automated unit and REST API tests covering dataset integrity, math logic, query routing, stress scenarios, and endpoint status codes. | Run `python -m unittest tests/test_retailmind.py`. |

---

## 4. Complete Solution to the Problem
| Requirement | Implementation in RetailMind AI | Verification Command / Evidence |
|---|---|---|
| **Small Retail Operation Focus** | Models 3 physical stores (Downtown, Mall, Airport) across 32 products and 6 categories with 92 days of sales history. | Data files in `data/*.csv`. |
| **Stock-Outs Before They Happen** | Automatically flags SKUs with &le; 7 days of inventory (e.g. Wireless Ergonomic Mouse at Mall Store with 4.94 days remaining). | Check Attention Center or ask *"What is running out?"*. |
| **Unmoving Stock Detection** | Automatically flags SKUs with &le; 5 units sold over 60 days holding &gt; 15 units in stock (e.g. Premium Fountain Pen Set). | Check Attention Center or ask *"Which products are slow moving?"*. |
| **Sales Spikes & Drops** | Compares rolling 7-day velocity against 30-day baseline, detecting surges (&ge; +40%) and drops (&le; -30%). | Check Attention Center or ask *"Which products had a sales spike?"*. |
| **Supporting Data & Calculations** | Every alert and copilot answer provides the exact formula and numbers (e.g. `12 / 2.43 = 4.94 days`). | Inspect calculation boxes and raw evidence drawer. |

---

## 5. Well-Grounded GenAI Implementation
| Requirement | Implementation in RetailMind AI | Verification Command / Evidence |
|---|---|---|
| **Zero LLM Hallucination of Numbers** | Python computes all numbers. Gemini is strictly used for natural language explanation and contextual recommendations. | Review `src/gemini_service.py` system prompts and grounding package. |
| **Gemini as Sole External AI API** | Gemini is the ONLY AI provider used. No OpenAI, Anthropic, Groq, Pinecone, or third-party RAG services. | Inspect `requirements.txt` and codebase. |
| **Evidence Traceability** | Every copilot answer provides dataset name, product SKU, store, date range, raw values, and intermediate math. | Inspect `View Raw Evidence` drawer on any copilot message card. |
| **Graceful Fallback** | If `GEMINI_API_KEY` is missing or rate-limited, deterministic natural language synthesis takes over without crashing. | Tested with and without `GEMINI_API_KEY`. Full application runs 100%. |

---

## 6. Strong Problem Understanding & Judgement
| Requirement | Implementation in RetailMind AI | Verification Command / Evidence |
|---|---|---|
| **Refusal of Causal Speculation** | When asked *"Why did sales decrease?"*, the system proves the drop but refuses to invent external causes (competitors, weather, marketing) not in data. | Tested in `test_difficult_demo_case_1_unsupported_cause`. |
| **Refusal of Distant Forecasts** | When asked *"What will our exact sales be six months from now?"*, the system declares the data insufficient rather than fabricating a prediction. | Tested in `test_difficult_demo_case_2_unsupported_forecast`. |
| **Human-in-the-Loop Safeguard** | The copilot recommends; the store manager decides. Never triggers automated purchases or price cuts without human approval. | Displayed on every attention card and copilot recommendation. |
| **Focus on Core Value** | Zero unnecessary bloat (no dummy auth, no payment gateways, no complex microservices). Maximizes reliability, precision, and judge usability. | Clean, fast, professional enterprise SaaS experience. |
