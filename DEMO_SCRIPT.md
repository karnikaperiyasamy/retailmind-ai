# RetailMind AI — Demo Video Presentation Script
**Duration**: 4 minutes 30 seconds (Target: 3–5 minutes)  
**Hackathon**: NexusTiQ24 • Track PS03: Retail — Sales and Inventory Copilot  
**Presenter**: RetailMind AI Team  

---

### [0:00 – 0:20] Hook & Problem Introduction
- **Visual**: Title screen showing RetailMind AI logo, tagline: *"Evidence-driven sales and inventory intelligence for retail managers."*
- **Speaker**:
  > *"Hello judges! A store manager's data is rich, but their daily decisions are rushed. Critical issues—like stockouts, excess inventory, and sudden demand shifts—are buried deep across spreadsheets and store registers. 
  > When managers turn to standard AI chatbots, they get hallucinations and made-up numbers. 
  > Today, we're introducing **RetailMind AI**: a sales and inventory copilot that never makes a claim without supporting figures and never guesses what the data cannot prove."*

---

### [0:20 – 0:50] Executive Dashboard Overview
- **Visual**: Browser at `http://localhost:8000`. Pan across the 6 top KPI cards and the 4 interactive charts.
- **Speaker**:
  > *"Here is the RetailMind AI dashboard running live on a single command—`python app.py`. 
  > The system loads 92 days of daily transactional history across 3 physical store locations—Downtown Flagship, Mall Store, and Airport Express—and 32 SKUs. 
  > Notice the KPI cards at the top: 30-day gross revenue of ₹7.87M, total physical stock of 6,290 units, and immediate flags for stock-out risks and overstocked inventory. 
  > Down below, the 90-day gross revenue trend, category share, and cross-store performance update deterministically from real sales logs."*

---

### [0:50 – 1:40] Normal Demo Scenario: "What is running out?"
- **Visual**: Click on the "AI Copilot" tab. Click the suggested prompt chip *"What is running out?"* or type it into the input bar.
- **Speaker**:
  > *"Let's test our copilot with the most critical retail question: **'What is running out?'**
  > Notice the speed and structure of the response. The system doesn't just give a chat message; it provides a structured decision card:
  > First, the **Answer**: It flags that Whole Bean Dark Roast at Downtown Store is depleted, and Wireless Ergonomic Mouse at the Mall Store has only 4.9 days of inventory left.
  > Second, look at the **Supporting Evidence**: Current stock is 12 units, with a 7-day average velocity of 2.43 units/day, against a reorder threshold of 25.
  > Third, the **Deterministic Calculation**: 12 / 2.43 = 4.94 days of inventory remaining. Python did that math, not the LLM.
  > Fourth, the **Recommendation**: It proposes a 51-unit replenishment order with supplier LogiGear Supplies, stating the assumption that demand remains steady.
  > And notice the expandable drawer: **'View Raw Evidence & Grounding Traceability'**, allowing a manager to audit the exact CSV records."*

---

### [1:40 – 2:20] Overstock Scenario: "Which products are overstocked?"
- **Visual**: Click the quick prompt *"Which products are overstocked?"*.
- **Speaker**:
  > *"Now, let's look at working capital efficiency: **'Which products are overstocked?'**
  > RetailMind AI immediately identifies Organic Cold Brew 1L at the Downtown Store. 
  > Current stock is 420 units. At current velocity of 3.71 units/day, this represents 113.2 days of supply—far exceeding the 30-day benchmark.
  > The system calculates an excess of 309 units, locking up ₹49,440.00 in working capital. 
  > It recommends freezing procurement and launching a promotional bundle to rebalance cash flow. Again, fully verifiable numbers."*

---

### [2:20 – 3:00] Difficult Demo Case 1: "Why did sales decrease?" (Uncertainty Handling)
- **Visual**: Click the stress test chip *"Why did sales decrease?"*.
- **Speaker**:
  > *"Now for the true test of responsible AI—a question that trips up almost every chatbot: **'Why did sales decrease?'**
  > Watch how RetailMind AI responds:
  > It confirms that sales for Artisan Ceramic Mug at Mall Store dropped by 62.7% (from 3.8 to 1.4 units/day).
  > BUT instead of inventing excuses—like blaming weather, competitor discounts, or marketing—it explicitly declares:
  > **'The available retail dataset does not contain sufficient causal information (such as foot traffic counters or competitor price tracking) to prove WHY this decline occurred.'**
  > It separates what the data proves from what it cannot prove. That is honest, responsible AI."*

---

### [3:00 – 3:30] Difficult Demo Case 2: "What will our exact sales be six months from now?"
- **Visual**: Click the second stress test chip *"What will our exact sales be six months from now?"*.
- **Speaker**:
  > *"Let's push it further: **'What will our exact sales be six months from now?'**
  > Most LLMs would hallucinate an exact future number. 
  > RetailMind AI refuses to fabricate predictions without evidence:
  > It points out that the dataset covers a 92-day horizon and that predicting 180 days out without macroeconomic models is statistically unsound. 
  > It recommends using rolling 30-day moving averages with supplier safety buffers instead of gambling working capital on guesses."*

---

### [3:30 – 4:00] Attention Center & Grounding Architecture
- **Visual**: Switch to the "Attention Center" tab and then "Stores" tab.
- **Speaker**:
  > *"Everything in RetailMind AI follows our strict grounding architecture:
  > Raw CSV Data &rarr; Local Semantic Retrieval with gemini-embedding-001 &rarr; Deterministic Python Analytics &rarr; Evidence Package &rarr; Gemini Natural Language Explanation.
  > Here in the Attention Center, alerts are categorized into Stockout Risks, Overstocks, Slow Movers, and Surges. 
  > Notice that every single card reinforces our **Human-in-the-Loop Safeguard**: the system recommends, but the store manager always signs off on physical orders."*

---

### [4:00 – 4:30] Deployment, Test Suite & Conclusion
- **Visual**: Show terminal running `python -m unittest tests/test_retailmind.py` (25/25 passing) and show `render.yaml` configuration.
- **Speaker**:
  > *"Under the hood: 25 automated unit and REST API tests pass in under 1 second. 
  > The application is pre-configured for Render deployment via `render.yaml` and starts locally with a single command: `python app.py`. 
  > RetailMind AI turns scattered retail data into evidence-backed actions without letting AI guess what the data cannot prove.
  > Thank you, and we look forward to your questions!"*
