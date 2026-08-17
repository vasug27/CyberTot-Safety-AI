import os
import sys
import json
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_generator import generate_labeled_dataset, generate_daily_stream_scenario
from src.classifier import CyberTotClassifier
from src.aggregator import ContextualRiskAggregator
from src.llm_summarizer import LLMSummarizer

def run_pipeline(scenario="grooming_attempt", launch_server=False):
    print("="*60)
    print("  CYBERTOT: PARENTAL CONTROL & CHILD SAFETY AI ENGINE")
    print("="*60)
    
    data_dir = "c:/Development/CyberTot/data"
    os.makedirs(data_dir, exist_ok=True)
    train_path = os.path.join(data_dir, "train.csv")
    
    if not os.path.exists(train_path):
        print("\n[Step 1/4] Generating synthetic Hinglish & English child activity dataset...")
        df = generate_labeled_dataset()
        train_size = int(0.8 * len(df))
        df.iloc[:train_size].to_csv(train_path, index=False)
        df.iloc[train_size:].to_csv(os.path.join(data_dir, "test.csv"), index=False)
    else:
        print("\n[Step 1/4] Synthetic dataset present.")

    model_path = "c:/Development/CyberTot/models/safety_classifier.joblib"
    if not os.path.exists(model_path):
        print("\n[Step 2/4] Training core local safety classifier (TF-IDF + Logistic Regression)...")
        import pandas as pd
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(os.path.join(data_dir, "test.csv"))
        
        clf = CyberTotClassifier()
        clf.fit(train_df["text"], train_df["label"])
        clf.evaluate(test_df["text"], test_df["label"])
        clf.save(model_path)
    else:
        print("\n[Step 2/4] Pre-trained classifier artifact loaded.")
        clf = CyberTotClassifier.load(model_path)

    print(f"\n[Step 3/4] Processing daily device event stream (Scenario: '{scenario}')...")
    stream_events = generate_daily_stream_scenario(scenario)
    aggregator = ContextualRiskAggregator(classifier=clf)
    analysis = aggregator.analyze_stream(stream_events)

    print("\n[Step 4/4] Generating parent-friendly daily briefing...")
    summarizer = LLMSummarizer()
    briefing = summarizer.generate_daily_parent_briefing(analysis)

    print("\n" + "="*60)
    print("  ANSWER 1: IS MY CHILD SAFE RIGHT NOW?")
    print("="*60)
    status_info = analysis["realtime_status"]
    print(f"Status:             {status_info['status']}")
    print(f"Headline:           {status_info['headline']}")
    print(f"Max Risk Score:     {status_info['max_risk_score']} / 100")
    print(f"Active Alert Count: {status_info['active_alerts_count']}")

    print("\n" + "="*60)
    print("  ANSWER 2: WHAT HAPPENED TODAY?")
    print("="*60)
    print(briefing)

    if launch_server:
        print("\nLaunching CyberTot Dashboard server at http://127.0.0.1:8000 ...")
        import uvicorn
        from src.app import app
        uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CyberTot AI System")
    parser.add_argument("--scenario", type=str, default="grooming_attempt", choices=["safe_day", "grooming_attempt", "cyberbullying", "scam_trap"])
    parser.add_argument("--server", action="store_true", help="Launch FastAPI web dashboard")
    args = parser.parse_args()
    
    run_pipeline(scenario=args.scenario, launch_server=args.server)
