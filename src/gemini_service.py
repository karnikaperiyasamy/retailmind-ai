"""
LLM Explanation & Grounding Service for RetailMind AI.
Supports both Groq and Google Gemini APIs with strict evidence grounding:
- Passes deterministic Python-computed facts and arithmetic to the LLM
- Forbids hallucination or fabrication of numbers
- Falls back gracefully to deterministic synthesis if APIs are offline or unconfigured
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional

logger = logging.getLogger("RetailMind.LLM")

class GeminiService:
    """
    Unified LLM Reasoning Service.
    Supports Groq (ultra-fast inference) and Google Gemini (Track PS03 specification)
    with 100% offline deterministic fallback.
    """
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY", "").strip()
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

        self.has_groq = bool(self.groq_key and self.groq_key != "your_groq_api_key_here")
        self.has_gemini = bool(self.gemini_key and self.gemini_key != "your_gemini_api_key_here")

        self.provider = "none"
        self.gemini_model = None

        if self.has_groq:
            self.provider = "groq"
            self.groq_model = "qwen/qwen3.8-27b"
            logger.info(f"LLM Service initialized with Groq API (model: {self.groq_model}).")
        elif self.has_gemini:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "max_output_tokens": 1024,
                    }
                )
                self.provider = "gemini"
                logger.info("LLM Service initialized with Google Gemini API (gemini-1.5-flash).")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}. Falling back to deterministic mode.")
                self.provider = "none"
        else:
            logger.info("No external LLM key configured. Deterministic zero-hallucination synthesis active.")

    @property
    def is_available(self) -> bool:
        return self.provider in ["groq", "gemini"]

    def generate_grounded_response(
        self,
        question: str,
        intent: str,
        evidence_package: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Routes query to active LLM provider or deterministic fallback."""
        if self.provider == "groq":
            try:
                return self._call_groq(question, intent, evidence_package)
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}. Falling back to deterministic synthesis.")
                return self._synthesize_deterministic(question, intent, evidence_package, fallback_reason=f"Groq: {e}")
        elif self.provider == "gemini" and self.gemini_model:
            try:
                return self._call_gemini(question, intent, evidence_package)
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Falling back to deterministic synthesis.")
                return self._synthesize_deterministic(question, intent, evidence_package, fallback_reason=f"Gemini: {e}")
        else:
            return self._synthesize_deterministic(question, intent, evidence_package)

    def _call_groq(
        self,
        question: str,
        intent: str,
        evidence_package: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calls Groq API with strict grounding instructions."""
        facts_summary = json.dumps(evidence_package, indent=2)

        system_prompt = (
            "You are RetailMind AI, an evidence-driven sales and inventory copilot for a retail store manager. "
            "STRICT RULES:\n"
            "1. NEVER invent or hallucinate any numbers, percentages, or dates.\n"
            "2. Use ONLY the facts provided in the EVIDENCE PACKAGE.\n"
            "3. If the user asks for causes (e.g. 'Why did sales decrease?'), state that the transaction records confirm the drop but do not record customer footfall or external causes.\n"
            "4. If the user asks for distant forecasts (e.g. 'What will sales be six months from now?'), state that the dataset does not contain sufficient information to predict six months out.\n"
            "5. You MUST return ONLY a JSON object with this exact schema:\n"
            "{\n"
            '  "answer": "A concise, clear paragraph explaining the findings.",\n'
            '  "recommendation": "Actionable next step for the store manager.",\n'
            '  "assumptions": ["Assumption 1"],\n'
            '  "limitations": ["Limitation 1"]\n'
            "}"
        )

        user_content = f"EVIDENCE PACKAGE:\n{facts_summary}\n\nUSER QUESTION:\n{question}"

        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"}
        }

        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Groq API error HTTP {resp.status_code}: {resp.text}")

        res_data = resp.json()
        raw_text = res_data["choices"][0]["message"]["content"].strip()
        parsed = json.loads(raw_text)

        return {
            "answer": parsed.get("answer", evidence_package.get("default_answer", "")),
            "evidence": evidence_package.get("evidence", []),
            "calculations": evidence_package.get("calculations", []),
            "recommendation": parsed.get("recommendation", evidence_package.get("default_recommendation", "")),
            "assumptions": parsed.get("assumptions", evidence_package.get("assumptions", [])),
            "limitations": parsed.get("limitations", evidence_package.get("limitations", [])),
            "intent": intent,
            "grounded": True,
            "engine": f"Groq ({self.groq_model} Grounded)"
        }

    def _call_gemini(
        self,
        question: str,
        intent: str,
        evidence_package: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prompts Gemini to explain the evidence without inventing numbers."""
        facts_summary = json.dumps(evidence_package, indent=2)

        prompt = f"""
You are the RetailMind AI Copilot for a store manager running 3 stores.
You must adhere strictly to these rules:
1. NEVER invent or hallucinate any numbers, percentages, currency figures, or dates.
2. Use ONLY the facts provided in the EVIDENCE PACKAGE below.
3. If the user asks for causes (e.g. "Why did sales decrease?"), state clearly that the transaction records confirm the drop but do not record customer footfall or external causes.
4. If the user asks for distant forecasts (e.g. "What will sales be six months from now?"), state that the dataset does not contain sufficient information to predict six months out.
5. Provide a helpful, clear natural-language explanation and actionable recommendation for a human store manager.

EVIDENCE PACKAGE:
{facts_summary}

USER QUESTION:
"{question}"

Please respond in valid JSON with this exact schema:
{{
  "answer": "A concise, natural-language paragraph summarizing the factual findings.",
  "recommendation": "The recommended operational next step for the store manager.",
  "assumptions": ["Assumption 1", "Assumption 2"],
  "limitations": ["Limitation or uncertainty 1"]
}}
"""
        response = self.gemini_model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            parsed = json.loads(text)
            return {
                "answer": parsed.get("answer", evidence_package.get("default_answer", "")),
                "evidence": evidence_package.get("evidence", []),
                "calculations": evidence_package.get("calculations", []),
                "recommendation": parsed.get("recommendation", evidence_package.get("default_recommendation", "")),
                "assumptions": parsed.get("assumptions", evidence_package.get("assumptions", [])),
                "limitations": parsed.get("limitations", evidence_package.get("limitations", [])),
                "intent": intent,
                "grounded": True,
                "engine": "Gemini 1.5 Flash (Grounded)"
            }
        except json.JSONDecodeError:
            return {
                "answer": text,
                "evidence": evidence_package.get("evidence", []),
                "calculations": evidence_package.get("calculations", []),
                "recommendation": evidence_package.get("default_recommendation", "Review data in Attention Center."),
                "assumptions": evidence_package.get("assumptions", []),
                "limitations": evidence_package.get("limitations", []),
                "intent": intent,
                "grounded": True,
                "engine": "Gemini 1.5 Flash"
            }

    def _synthesize_deterministic(
        self,
        question: str,
        intent: str,
        evidence_package: Dict[str, Any],
        fallback_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pure Python natural-language synthesis when external LLMs are offline.
        Guarantees 100% uptime, zero hallucination, and instant response.
        """
        limitations = list(evidence_package.get("limitations", []))
        if not self.is_available:
            limitations.append("LLM API key not configured in environment. Operating in zero-hallucination deterministic mode.")
        elif fallback_reason:
            limitations.append(f"External service note: {fallback_reason}. Answer synthesized via deterministic engine.")

        return {
            "answer": evidence_package.get("default_answer", "Analysis completed based on current store records."),
            "evidence": evidence_package.get("evidence", []),
            "calculations": evidence_package.get("calculations", []),
            "recommendation": evidence_package.get("default_recommendation", "Store manager should verify current shelf stock."),
            "assumptions": evidence_package.get("assumptions", [
                "Assumes recent 7-day sales rate reflects near-term demand.",
                "Assumes current inventory records in inventory.csv are accurate."
            ]),
            "limitations": limitations,
            "intent": intent,
            "grounded": True,
            "engine": "Deterministic Analytics Engine (Offline Mode)"
        }
