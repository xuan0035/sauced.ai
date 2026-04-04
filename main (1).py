"""
RecipeAgent Backend — FastAPI server
Orchestrates 3 Fetch.AI uAgents:
  - Agent 1: Scraper (Browser Use + Substack)
  - Agent 2: Nutrition Matcher (Edamam API)
  - Agent 3: Meal Planner (scaling + shopping list)
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import uuid
from datetime import datetime

from models import (
    UserProfile, ScrapeRequest, MatchRequest,
    MealPlanRequest, JobStatus, RecipeResult, MealPlan
)
from agents.scraper_agent import ScraperAgent
from agents.nutrition_agent import NutritionAgent
from agents.planner_agent import PlannerAgent

app = FastAPI(
    title="RecipeAgent API",
    description="Fetch.AI + Browser Use powered recipe matching system",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (replace with Redis/DB in production)
jobs: dict[str, JobStatus] = {}

scraper = ScraperAgent()
nutrition = NutritionAgent()
planner = PlannerAgent()


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ─── Agent 1: Scraper ─────────────────────────────────────────────────────────

@app.post("/api/scrape", response_model=dict)
async def scrape_substack(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Kick off a Browser Use scrape of a Substack food newsletter URL.
    Returns a job_id to poll for results.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(
        job_id=job_id, status="pending", agent="scraper",
        created_at=datetime.utcnow().isoformat()
    )
    background_tasks.add_task(_run_scrape, job_id, req)
    return {"job_id": job_id, "status": "pending"}


async def _run_scrape(job_id: str, req: ScrapeRequest):
    jobs[job_id].status = "running"
    try:
        recipes = await scraper.scrape(req.url, req.max_recipes)
        jobs[job_id].status = "complete"
        jobs[job_id].result = recipes
    except Exception as e:
        jobs[job_id].status = "error"
        jobs[job_id].error = str(e)


# ─── Agent 2: Nutrition Matcher ───────────────────────────────────────────────

@app.post("/api/match", response_model=dict)
async def match_recipes(req: MatchRequest, background_tasks: BackgroundTasks):
    """
    Given scraped recipes + user profile, score and rank recipes via Edamam.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(
        job_id=job_id, status="pending", agent="nutrition_matcher",
        created_at=datetime.utcnow().isoformat()
    )
    background_tasks.add_task(_run_match, job_id, req)
    return {"job_id": job_id, "status": "pending"}


async def _run_match(job_id: str, req: MatchRequest):
    jobs[job_id].status = "running"
    try:
        matched = await nutrition.match(req.recipes, req.profile)
        jobs[job_id].status = "complete"
        jobs[job_id].result = matched
    except Exception as e:
        jobs[job_id].status = "error"
        jobs[job_id].error = str(e)


# ─── Agent 3: Meal Planner ────────────────────────────────────────────────────

@app.post("/api/plan", response_model=dict)
async def generate_meal_plan(req: MealPlanRequest, background_tasks: BackgroundTasks):
    """
    Scales top-matched recipes to meal prep quantity, generates shopping list.
    Optionally places Instacart order.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(
        job_id=job_id, status="pending", agent="meal_planner",
        created_at=datetime.utcnow().isoformat()
    )
    background_tasks.add_task(_run_plan, job_id, req)
    return {"job_id": job_id, "status": "pending"}


async def _run_plan(job_id: str, req: MealPlanRequest):
    jobs[job_id].status = "running"
    try:
        plan = await planner.plan(req.matched_recipes, req.profile, req.servings_per_recipe)
        jobs[job_id].status = "complete"
        jobs[job_id].result = plan
    except Exception as e:
        jobs[job_id].status = "error"
        jobs[job_id].error = str(e)


# ─── Full Pipeline ────────────────────────────────────────────────────────────

@app.post("/api/pipeline", response_model=dict)
async def run_full_pipeline(
    substack_url: str,
    profile: UserProfile,
    background_tasks: BackgroundTasks,
    max_recipes: int = 10,
    servings: int = 4
):
    """
    Runs all 3 agents in sequence: Scrape → Match → Plan.
    Returns a single job_id to track the full pipeline.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(
        job_id=job_id, status="pending", agent="pipeline",
        created_at=datetime.utcnow().isoformat()
    )
    background_tasks.add_task(_run_pipeline, job_id, substack_url, profile, max_recipes, servings)
    return {"job_id": job_id, "status": "pending"}


async def _run_pipeline(job_id, url, profile, max_recipes, servings):
    try:
        jobs[job_id].status = "scraping"
        recipes = await scraper.scrape(url, max_recipes)

        jobs[job_id].status = "matching"
        matched = await nutrition.match(recipes, profile)

        jobs[job_id].status = "planning"
        plan = await planner.plan(matched, profile, servings)

        jobs[job_id].status = "complete"
        jobs[job_id].result = {
            "scraped_count": len(recipes),
            "matched_recipes": matched,
            "meal_plan": plan,
        }
    except Exception as e:
        jobs[job_id].status = "error"
        jobs[job_id].error = str(e)


# ─── Job Polling ──────────────────────────────────────────────────────────────

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/jobs")
async def list_jobs():
    return list(jobs.values())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
