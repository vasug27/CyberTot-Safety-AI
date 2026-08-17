import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import dateutil.parser
from datetime import datetime
from src.classifier import CyberTotClassifier

class ContextualRiskAggregator:
    def __init__(self, classifier=None):
        self.classifier = classifier or CyberTotClassifier.load()

    def _get_time_multiplier(self, ts_str):
        """Calculates late night risk multiplier (10 PM - 5 AM)."""
        try:
            dt = dateutil.parser.parse(ts_str)
            hour = dt.hour
            if hour >= 22 or hour < 5:
                return 1.6
            elif hour >= 20:
                return 1.2
            return 1.0
        except Exception:
            return 1.0

    def _get_counterparty_multiplier(self, counterparty):
        """Calculates anonymity risk multiplier."""
        if not counterparty:
            return 1.0
        counterparty_lower = counterparty.lower()
        if "unknown" in counterparty_lower or "stranger" in counterparty_lower or "bot" in counterparty_lower:
            return 1.8
        elif "group" in counterparty_lower:
            return 1.2
        return 1.0

    def process_event(self, event):
        enriched = dict(event)
        event_type = event.get("type")
        
        base_score = 0.0
        category = "safe"
        confidence = 1.0

        if event_type == "chat_message":
            text = event.get("text", "")
            probas = self.classifier.predict_proba([text])[0]
            class_prob_map = {cls: prob for cls, prob in zip(self.classifier.classes_, probas)}
            
            pred_cat = self.classifier.predict([text])[0]
            category = pred_cat
            confidence = float(class_prob_map.get(pred_cat, 0.5))

            if category != "safe":
                severity_map = {
                    "grooming": 90.0,
                    "distress_selfharm": 85.0,
                    "inappropriate_content": 75.0,
                    "cyberbullying": 60.0,
                    "scam_phishing": 50.0
                }
                base_score = severity_map.get(category, 50.0) * confidence
            else:
                base_score = 0.0

            time_mult = self._get_time_multiplier(event.get("ts", ""))
            cparty_mult = self._get_counterparty_multiplier(event.get("counterparty", ""))
            
            final_score = min(100.0, base_score * time_mult * cparty_mult)
            
            enriched.update({
                "classified_category": category,
                "confidence": round(confidence, 2),
                "risk_score": round(final_score, 1),
                "context_flags": {
                    "is_late_night": time_mult > 1.0,
                    "is_unknown_sender": cparty_mult > 1.0
                }
            })

        elif event_type == "web_visit":
            title = event.get("title", "")
            domain = event.get("domain", "")
            full_text = f"{domain} {title}"
            
            pred_cat = self.classifier.predict([full_text])[0]
            category = pred_cat
            
            if "free" in title.lower() or "robux" in title.lower() or "card" in title.lower() or "generator" in domain:
                category = "scam_phishing"
                base_score = 75.0
            elif pred_cat != "safe":
                base_score = 65.0
            else:
                base_score = 0.0

            enriched.update({
                "classified_category": category,
                "confidence": 0.90 if base_score > 0 else 0.99,
                "risk_score": base_score,
                "context_flags": {}
            })

        elif event_type == "app_session":
            duration_s = event.get("duration_s", 0)
            app = event.get("app", "")
            
            if duration_s > 5400 and ("roblox" in app or "freefire" in app or "minecraft" in app):
                category = "excessive_screentime"
                base_score = 35.0
            else:
                category = "safe"
                base_score = 0.0

            enriched.update({
                "classified_category": category,
                "confidence": 1.0,
                "risk_score": base_score,
                "context_flags": {
                    "long_duration": duration_s > 5400
                }
            })

        return enriched

    def analyze_stream(self, stream_events):
        processed_events = [self.process_event(ev) for ev in stream_events]
        
        flagged_events = [ev for ev in processed_events if ev.get("risk_score", 0) >= 30.0]
        max_risk_event = max(processed_events, key=lambda x: x.get("risk_score", 0)) if processed_events else None
        max_risk_score = max_risk_event.get("risk_score", 0) if max_risk_event else 0.0

        if max_risk_score >= 65.0:
            status = "DANGER"
            headline = "Action Required: Potential Severe Risk Detected"
        elif max_risk_score >= 35.0:
            status = "CAUTION"
            headline = "Attention: Mild Risk Flags Detected Today"
        else:
            status = "SAFE"
            headline = "Child is Safe: Normal Activity Patterns"

        app_screentime = {}
        for ev in processed_events:
            if ev.get("type") == "app_session":
                app_name = ev.get("app", "other").split(".")[-1].capitalize()
                dur_min = round(ev.get("duration_s", 0) / 60, 1)
                app_screentime[app_name] = app_screentime.get(app_name, 0) + dur_min

        category_counts = {}
        for ev in processed_events:
            cat = ev.get("classified_category", "safe")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "realtime_status": {
                "status": status,
                "headline": headline,
                "max_risk_score": max_risk_score,
                "active_alerts_count": len(flagged_events),
                "top_risk_event": max_risk_event
            },
            "today_summary": {
                "total_events_processed": len(processed_events),
                "flagged_events_count": len(flagged_events),
                "category_counts": category_counts,
                "app_screentime_minutes": app_screentime,
                "flagged_events_list": flagged_events,
                "all_processed_events": processed_events
            }
        }

if __name__ == "__main__":
    import json
    with open("c:/Development/CyberTot/data/sample_daily_stream.json") as f:
        stream = json.load(f)
    
    aggregator = ContextualRiskAggregator()
    results = aggregator.analyze_stream(stream)
    print("\n--- Stream Analysis Summary ---")
    print(f"Status: {results['realtime_status']['status']}")
    print(f"Headline: {results['realtime_status']['headline']}")
    print(f"Flagged Events: {results['today_summary']['flagged_events_count']}")
