import os
import sys
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.aggregator import ContextualRiskAggregator

class LLMSummarizer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("Gemini API client initialized successfully.")
            except Exception as e:
                print(f"Could not initialize Gemini client: {e}. Using deterministic fallback summarizer.")
        else:
            print("No GEMINI_API_KEY found. Running with deterministic rule-based LLM fallback generator.")

    def generate_daily_parent_briefing(self, analysis_results):
        status_info = analysis_results.get("realtime_status", {})
        summary_info = analysis_results.get("today_summary", {})
        
        status = status_info.get("status", "SAFE")
        flagged_list = summary_info.get("flagged_events_list", [])
        screentime = summary_info.get("app_screentime_minutes", {})
        
        filtered_alerts_for_llm = []
        for ev in flagged_list:
            filtered_alerts_for_llm.append({
                "time": ev.get("ts"),
                "app": ev.get("app"),
                "category": ev.get("classified_category"),
                "risk_score": ev.get("risk_score"),
                "context": ev.get("context_flags")
            })

        prompt = f"""
You are CyberTot AI, an empathetic, supportive parental assistant for Indian parents with children aged 8-14.
Summarize today's child activity data into two clear sections:

1. **Is My Child Safe Right Now?**: Direct status answer ({status}) with a 2-sentence explanation of current active risks and recommended parent action.
2. **What Happened Today?**: A warm, bulleted summary of digital activity (screen time, gaming, chat trends, and any flagged safety alerts).

Data Summary:
- Safety Status: {status}
- Total Events Analyzed Locally: {summary_info.get('total_events_processed')}
- Screen Time Minutes: {json.dumps(screentime)}
- Aggregated Risk Alerts ({len(filtered_alerts_for_llm)}): {json.dumps(filtered_alerts_for_llm)}

Write in simple, clear language for parents. Be supportive, non-alarmist, and practical.
"""

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                print(f"Gemini API invocation failed: {e}. Using fallback generator.")

        return self._generate_fallback_summary(status, flagged_list, screentime)

    def _generate_fallback_summary(self, status, flagged_list, screentime):
        top_apps = ", ".join([f"{app} ({mins} min)" for app, mins in screentime.items()]) or "Minimal app activity"
        
        if status == "DANGER":
            return f"""### Safety Status: High Attention Required

**Is My Child Safe Right Now?**
No, urgent attention is recommended. A high-priority risk alert was detected today involving suspicious communications from an unknown account during late-night hours. We advise calmly talking with your child without scolding them.

**What Happened Today?**
* **Digital Activity:** Main screen time was recorded on {top_apps}.
* **Flagged Safety Alerts:** {len(flagged_list)} event(s) were flagged by the local security model.
* **Key Concern:** Contact from an unrecognized user asking for social media handles and requesting secrecy.
* **Parental Action Tip:** Remind your child that they can always share online conversations with you without fear of losing their device privileges."""

        elif status == "CAUTION":
            return f"""### Safety Status: Mild Caution

**Is My Child Safe Right Now?**
Your child is generally safe, but mild activity flags were detected today (e.g. elevated gaming trash-talk or visiting unverified promo links).

**What Happened Today?**
* **Digital Activity:** App usage was centered around {top_apps}.
* **Flagged Safety Alerts:** {len(flagged_list)} mild alert(s) detected.
* **Key Concern:** Gaming frustration or exposure to promotional clickbait.
* **Parental Action Tip:** Check in with your child about how their gaming sessions went today and encourage healthy breaks."""

        else:
            return f"""### Safety Status: Child is Safe

**Is My Child Safe Right Now?**
Yes, your child is safe! All digital activity today strictly matched normal, healthy interaction patterns with verified friends and trusted educational/gaming content.

**What Happened Today?**
* **Digital Activity:** Balanced digital session on {top_apps}.
* **Flagged Safety Alerts:** Zero safety violations or risk triggers detected.
* **Parental Action Tip:** Great day! No intervention needed."""

if __name__ == "__main__":
    with open("c:/Development/CyberTot/data/sample_daily_stream.json") as f:
        stream = json.load(f)
    
    agg = ContextualRiskAggregator()
    results = agg.analyze_stream(stream)
    
    summarizer = LLMSummarizer()
    briefing = summarizer.generate_daily_parent_briefing(results)
    print("\n--- LLM Summary Briefing ---")
    print(briefing)
