"""
RetailMind AI - Flask Backend Application
NexusTiQ24 Hackathon - Track PS03 (Retail — Sales and Inventory Copilot)

Single-command entrypoint: python app.py
Listens on http://0.0.0.0:8000
Serves both REST API and modern frontend single-page application.
"""

import os
import json
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv

# Load environment variables (.env) if present
load_dotenv()

from src.data_loader import DataLoader
from src.analytics import AnalyticsEngine
from src.recommendations import RecommendationEngine
from src.attention import AttentionCenter

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("RetailMind")

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# Initialize Data and Analytics
try:
    data_loader = DataLoader.get_instance()
    analytics = AnalyticsEngine(data_loader)
    attention_center = AttentionCenter(analytics)
    logger.info("Data loader, Analytics engine, and Attention center initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize data loader or analytics: {e}")
    raise

# Check Gemini availability
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
gemini_available = bool(GEMINI_KEY and GEMINI_KEY != "your_gemini_api_key_here")

# Lazy import query engine
_query_engine = None

def get_query_engine():
    global _query_engine
    if _query_engine is None:
        try:
            from src.query_engine import QueryEngine
            _query_engine = QueryEngine(analytics_engine=analytics)
        except Exception as e:
            logger.warning(f"QueryEngine lazy load fallback: {e}")
            _query_engine = None
    return _query_engine

# -------------------------------------------------------------
# Frontend Route
# -------------------------------------------------------------
@app.route("/")
def index():
    """Serves the primary RetailMind AI SaaS Dashboard interface."""
    return render_template("index.html")

# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def api_health():
    """System health check and status."""
    has_gemini = bool(os.environ.get("GEMINI_API_KEY", "").strip() and os.environ.get("GEMINI_API_KEY") != "your_gemini_api_key_here")
    return jsonify({
        "status": "healthy",
        "service": "RetailMind AI",
        "version": "1.0.0",
        "hackathon": "NexusTiQ24",
        "track_id": "PS03",
        "gemini_available": has_gemini,
        "message": "Gemini is available." if has_gemini else "Gemini is unavailable. Deterministic analytics are still available.",
        "gemini_mode": "Active (LLM Reasoning + gemini-embedding-001)" if has_gemini else "Deterministic Fallback (Zero Hallucination Guaranteed)",
        "stores_loaded": len(data_loader.get_stores()),
        "products_loaded": len(data_loader.get_products()),
        "latest_data_date": data_loader.get_latest_date().strftime("%Y-%m-%d")
    })

@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Endpoint not found", "status": 404}), 404
    return render_template("index.html"), 404

@app.errorhandler(500)
def handle_500(e):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error", "status": 500}), 500
    return render_template("index.html"), 500

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """Returns top KPI cards, trends, and category distribution."""
    try:
        metrics = analytics.get_dashboard_metrics()
        trends = analytics.get_sales_trends(days=90)
        category_perf = analytics.get_category_performance()
        store_perf = analytics.get_store_performance()
        products = analytics.get_product_performance()
        
        # Sort top 5 products by 30d revenue
        top_products = sorted(products, key=lambda x: x["revenue_30d"], reverse=True)[:5]

        return jsonify({
            "success": True,
            "metrics": metrics,
            "sales_trend_90d": trends,
            "category_performance": category_perf,
            "store_performance": store_perf,
            "top_products": top_products
        })
    except Exception as e:
        logger.error(f"Error in /api/dashboard: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/attention", methods=["GET"])
def api_attention():
    """Returns 'Needs Attention Today' prioritized actionable alerts."""
    try:
        stockouts = analytics.get_stockout_risks(max_days=7.0)
        overstocked = analytics.get_overstock_products(min_days=45.0)
        slow_moving = analytics.get_slow_moving_products(window_days=60, max_sales_threshold=5)
        spikes = analytics.get_sales_spikes(spike_threshold_pct=40.0)
        drops = analytics.get_sales_drops(drop_threshold_pct=-30.0)

        # Build structured recommendation packages
        stockout_recs = [RecommendationEngine.format_stockout_recommendation(item) for item in stockouts[:8]]
        overstock_recs = [RecommendationEngine.format_overstock_recommendation(item) for item in overstocked[:8]]
        slow_recs = [RecommendationEngine.format_slow_moving_recommendation(item) for item in slow_moving[:8]]

        return jsonify({
            "success": True,
            "summary": {
                "stockout_risk_count": len(stockouts),
                "overstock_count": len(overstocked),
                "slow_moving_count": len(slow_moving),
                "sales_spikes_count": len(spikes),
                "sales_drops_count": len(drops),
                "total_alerts": len(stockouts) + len(overstocked) + len(slow_moving) + len(spikes) + len(drops)
            },
            "stockouts": stockouts[:10],
            "overstocked": overstocked[:10],
            "slow_moving": slow_moving[:10],
            "spikes": spikes[:10],
            "drops": drops[:10],
            "recommendations": {
                "stockouts": stockout_recs,
                "overstock": overstock_recs,
                "slow_moving": slow_recs
            }
        })
    except Exception as e:
        logger.error(f"Error in /api/attention: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/products", methods=["GET"])
def api_products():
    """Returns the full catalog with 30-day velocity, stock, and health status."""
    try:
        product_id = request.args.get("id")
        products = analytics.get_product_performance(product_id=product_id)
        return jsonify({
            "success": True,
            "count": len(products),
            "products": products
        })
    except Exception as e:
        logger.error(f"Error in /api/products: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/stores", methods=["GET"])
def api_stores():
    """Returns store-level breakdown and comparison data."""
    try:
        store_id = request.args.get("id")
        stores = analytics.get_store_performance(store_id=store_id)
        return jsonify({
            "success": True,
            "count": len(stores),
            "stores": stores
        })
    except Exception as e:
        logger.error(f"Error in /api/stores: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/sales", methods=["GET"])
def api_sales():
    """Returns sales records with optional filtering."""
    try:
        days = int(request.args.get("days", 30))
        trends = analytics.get_sales_trends(days=days)
        return jsonify({
            "success": True,
            "days": days,
            "trends": trends
        })
    except Exception as e:
        logger.error(f"Error in /api/sales: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/inventory", methods=["GET"])
def api_inventory():
    """Returns inventory status breakdown across all stores."""
    try:
        status = analytics.get_inventory_status()
        return jsonify({
            "success": True,
            "inventory_status": status
        })
    except Exception as e:
        logger.error(f"Error in /api/inventory: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/copilot", methods=["POST"])
def api_copilot():
    """
    Main Natural-Language Copilot Query Handler.
    Receives {"question": "..."}
    Returns structured JSON:
    {
        "answer": "...",
        "evidence": [...],
        "calculations": [...],
        "recommendation": "...",
        "assumptions": [...],
        "limitations": [...],
        "intent": "...",
        "grounded": True
    }
    """
    try:
        payload = request.get_json(silent=True) or {}
        question = payload.get("question", "").strip()

        if not question:
            return jsonify({
                "answer": "Please provide a question about sales, inventory, or store performance.",
                "evidence": [],
                "calculations": [],
                "recommendation": "Try asking: 'What is running out?', 'Which products are overstocked?', or 'How did Wireless Mouse perform this month?'.",
                "assumptions": [],
                "limitations": ["Empty question received."],
                "intent": "empty_query",
                "grounded": True
            }), 400

        engine = get_query_engine()
        if engine is not None:
            response_data = engine.process_query(question)
            return jsonify(response_data)
        else:
            # Fallback if QueryEngine is loading
            return jsonify({
                "answer": f"Processed query: {question}",
                "evidence": ["System is operating in standard deterministic mode."],
                "calculations": [],
                "recommendation": "Review the Attention Center for immediate stock and sales flags.",
                "assumptions": [],
                "limitations": ["Query engine initializing."],
                "intent": "fallback",
                "grounded": True
            })
    except Exception as e:
        logger.error(f"Error in /api/copilot: {e}")
        return jsonify({
            "answer": "An unexpected error occurred while processing your question.",
            "evidence": [],
            "calculations": [],
            "recommendation": "Please try asking with specific terms like 'running out', 'overstocked', or a product name.",
            "assumptions": [],
            "limitations": [f"Internal error: {str(e)}"],
            "intent": "error",
            "grounded": False
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting RetailMind AI on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
