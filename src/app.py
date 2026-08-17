import os
import sys
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_generator import generate_daily_stream_scenario
from src.aggregator import ContextualRiskAggregator
from src.llm_summarizer import LLMSummarizer

app = FastAPI(title="CyberTot AI - Parental Control & Child Safety System", version="1.0.0")

aggregator = ContextualRiskAggregator()
summarizer = LLMSummarizer()

templates = Jinja2Templates(directory="src/templates")

current_scenario = "grooming_attempt"
current_stream = generate_daily_stream_scenario(current_scenario)

class TextClassifyRequest(BaseModel):
    text: str

class ScenarioRequest(BaseModel):
    scenario: str

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/analysis")
async def get_analysis():
    results = aggregator.analyze_stream(current_stream)
    briefing = summarizer.generate_daily_parent_briefing(results)
    return JSONResponse({
        "scenario": current_scenario,
        "realtime_status": results["realtime_status"],
        "today_summary": results["today_summary"],
        "parent_briefing": briefing
    })

@app.post("/api/simulate")
async def simulate_scenario(req: ScenarioRequest):
    global current_scenario, current_stream
    valid_scenarios = ["safe_day", "grooming_attempt", "cyberbullying", "scam_trap"]
    if req.scenario not in valid_scenarios:
        return JSONResponse({"error": "Invalid scenario type"}, status_code=400)
    
    current_scenario = req.scenario
    current_stream = generate_daily_stream_scenario(current_scenario)
    
    results = aggregator.analyze_stream(current_stream)
    briefing = summarizer.generate_daily_parent_briefing(results)
    
    return JSONResponse({
        "status": "success",
        "scenario": current_scenario,
        "realtime_status": results["realtime_status"],
        "today_summary": results["today_summary"],
        "parent_briefing": briefing
    })

@app.post("/api/classify_text")
async def classify_text(req: TextClassifyRequest):
    if not req.text.strip():
        return JSONResponse({"error": "Text cannot be empty"}, status_code=400)
    
    event = {
        "ts": "2026-08-11T23:15:00+05:30",
        "type": "chat_message",
        "app": "com.whatsapp",
        "text": req.text,
        "counterparty": "unknown_user"
    }
    enriched = aggregator.process_event(event)
    return JSONResponse(enriched)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
