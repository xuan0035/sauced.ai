# RecipeAgent 🍽

> Fetch.AI + Browser Use powered recipe matching from Substack food newsletters

---

## Architecture

```
┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐
│   Frontend   │───▶│  FastAPI Backend  │───▶│  Fetch.AI uAgents │
│  (index.html)│    │    (main.py)      │    │  (3 agents)       │
└──────────────┘    └──────────────────┘    └───────────────────┘
```

### 3 Agents

| # | Agent | Owner | Stack |
|---|-------|-------|-------|
| 1 | **Scraper** | Person 2 | Browser Use + LLM |
| 2 | **Nutrition Matcher** | Person 2 | Edamam API |
| 3 | **Meal Planner** | Person 1 | Fetch.AI uAgents |

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in your API keys in .env

uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
# Just open frontend/index.html in a browser, OR:
cd frontend
npx serve .
```

---

## API Keys Needed

| Service | Who Gets It | Link |
|---------|-------------|------|
| Edamam Nutrition | Person 2 | https://developer.edamam.com/ |
| OpenAI (for Browser Use) | Person 2 | https://platform.openai.com |
| Fetch.AI Agentverse | Person 1 | https://agentverse.ai |
| Instacart Partner API | TBD | (Requires approval) |

---

## Team TODO

### Person 1 — Fetch.AI uAgents
- [ ] Register 3 agents on Agentverse
- [ ] Wire the 3 agents together with message passing (uagents `@agent.on_message`)
- [ ] Replace the background task pattern in `main.py` with Fetch.AI message bus
- [ ] Integrate Meal Planner with Instacart API when available

### Person 2 — Browser Use + Edamam
- [ ] Install browser-use: `pip install browser-use`
- [ ] Uncomment Browser Use imports in `agents/scraper_agent.py`
- [ ] Implement `_parse_result()` to parse Browser Use JSON output
- [ ] Set EDAMAM_APP_ID + EDAMAM_APP_KEY in .env
- [ ] Uncomment Edamam call in `agents/nutrition_agent.py`

### Person 3 — Frontend + Demo
- [ ] Connect frontend API calls to real backend URL
- [ ] Polish loading states and error messages
- [ ] Add recipe image display (Unsplash fallback?)
- [ ] Prepare demo script and slideshow

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/scrape` | Kick off Browser Use scrape |
| POST | `/api/match` | Score recipes against profile |
| POST | `/api/plan` | Generate scaled meal plan |
| POST | `/api/pipeline` | Run all 3 agents |
| GET | `/api/jobs/{id}` | Poll job status |
| GET | `/health` | Health check |

---

## Demo Flow

1. Fill in profile (macros, restrictions, cuisine prefs)
2. Paste Substack URL → Run Full Pipeline
3. View matched recipes sorted by score
4. Review weekly meal plan + shopping list
5. Click "Order on Instacart" (demo link)
