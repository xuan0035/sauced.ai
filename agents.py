"""
agents.py — sauced.ai Fetch.AI uAgent definitions
Run all three agents + orchestrator together:
  python agents.py

Requirements:
  pip install uagents httpx
"""

import asyncio
import httpx
from uagents import Agent, Context, Model, Bureau

# ---------------------------------------------------------------------------
# Message models
# ---------------------------------------------------------------------------

class ScrapeRequest(Model):
    substack_url: str
    max_recipes: int = 10

class ScrapeResult(Model):
    recipes: list[dict]

class MatchRequest(Model):
    recipes: list[dict]
    profile: dict

class MatchResult(Model):
    matched_recipes: list[dict]

class PlanRequest(Model):
    matched_recipes: list[dict]
    profile: dict

class PlanResult(Model):
    meal_plan: dict


# ---------------------------------------------------------------------------
# Agent addresses (fixed via seed so they never change)
# ---------------------------------------------------------------------------

SCRAPER_SEED  = "sauced_scraper_agent_seed_v1"
MATCHER_SEED  = "sauced_matcher_agent_seed_v1"
PLANNER_SEED  = "sauced_planner_agent_seed_v1"
ORCH_SEED     = "sauced_orchestrator_seed_v1"


# ---------------------------------------------------------------------------
# Agent 1 — Scraper
# Scrapes Substack for recipes using browser-use
# ---------------------------------------------------------------------------

scraper = Agent(
    name="scraper_agent",
    seed=SCRAPER_SEED,
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)

@scraper.on_event("startup")
async def scraper_startup(ctx: Context):
    ctx.logger.info(f"Scraper agent started — address: {scraper.address}")

@scraper.on_message(model=ScrapeRequest, replies=ScrapeResult)
async def handle_scrape(ctx: Context, sender: str, msg: ScrapeRequest):
    ctx.logger.info(f"Scraping {msg.substack_url}")

    # TODO: Replace stub with real browser-use scraping:
    #
    # from browser_use import Browser, BrowserConfig
    # from browser_use.agent.service import Agent as BrowserAgent
    # from langchain_openai import ChatOpenAI
    #
    # browser = Browser(config=BrowserConfig(headless=True))
    # llm = ChatOpenAI(model="gpt-4o")
    # task = f"""Go to {msg.substack_url}/archive and find all recipe posts.
    #            For each recipe post click into it and extract:
    #            - Post title
    #            - List of ingredients with amounts and units
    #            - Step-by-step instructions
    #            - Number of servings
    #            Return as structured JSON list."""
    # agent = BrowserAgent(task=task, llm=llm, browser=browser)
    # result = await agent.run()
    # recipes = parse_browser_result(result.final_result())

    # Stub recipes for demo
    recipes = [
        {
            "id": "r1",
            "title": "Miso Glazed Salmon",
            "source_url": f"{msg.substack_url}/p/miso-salmon",
            "ingredients": [
                {"name": "salmon fillet", "amount": 6, "unit": "oz"},
                {"name": "white miso paste", "amount": 2, "unit": "tbsp"},
                {"name": "mirin", "amount": 1, "unit": "tbsp"},
                {"name": "soy sauce", "amount": 1, "unit": "tbsp"},
                {"name": "sesame oil", "amount": 1, "unit": "tsp"},
            ],
            "servings": 2,
            "instructions": [
                "Whisk miso, mirin, soy sauce, and sesame oil into a glaze.",
                "Coat salmon fillets evenly and marinate for 30 minutes.",
                "Broil on high for 8 minutes until caramelized.",
            ],
            "tags": ["Japanese", "seafood", "high-protein"],
        },
        {
            "id": "r2",
            "title": "Thai Basil Chicken",
            "source_url": f"{msg.substack_url}/p/pad-krapow",
            "ingredients": [
                {"name": "ground chicken", "amount": 1, "unit": "lb"},
                {"name": "Thai basil leaves", "amount": 1, "unit": "cup"},
                {"name": "fish sauce", "amount": 2, "unit": "tbsp"},
                {"name": "oyster sauce", "amount": 1, "unit": "tbsp"},
                {"name": "garlic cloves", "amount": 4, "unit": "cloves"},
                {"name": "Thai bird chilis", "amount": 3, "unit": "pieces"},
            ],
            "servings": 2,
            "instructions": [
                "Pound garlic and chilis in mortar until paste forms.",
                "Fry paste in hot wok 30 seconds until fragrant.",
                "Add chicken, break apart, cook through. Add sauces, toss with basil.",
            ],
            "tags": ["Thai", "spicy", "high-protein", "quick"],
        },
    ]

    ctx.logger.info(f"Scraped {len(recipes)} recipes")
    await ctx.send(sender, ScrapeResult(recipes=recipes))


# ---------------------------------------------------------------------------
# Agent 2 — Nutrition Matcher
# Calls Edamam API and scores recipes against user profile
# ---------------------------------------------------------------------------

matcher = Agent(
    name="matcher_agent",
    seed=MATCHER_SEED,
    port=8002,
    endpoint=["http://localhost:8002/submit"],
)

@matcher.on_event("startup")
async def matcher_startup(ctx: Context):
    ctx.logger.info(f"Matcher agent started — address: {matcher.address}")

@matcher.on_message(model=MatchRequest, replies=MatchResult)
async def handle_match(ctx: Context, sender: str, msg: MatchRequest):
    ctx.logger.info(f"Matching {len(msg.recipes)} recipes against profile")
    profile = msg.profile

    # TODO: Replace stub with real Edamam API calls:
    #
    # EDAMAM_APP_ID  = os.getenv("EDAMAM_APP_ID")
    # EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY")
    #
    # async with httpx.AsyncClient() as client:
    #     for recipe in msg.recipes:
    #         ingr_strings = [f"{i['amount']} {i['unit']} {i['name']}" for i in recipe["ingredients"]]
    #         resp = await client.post(
    #             "https://api.edamam.com/api/nutrition-details",
    #             params={"app_id": EDAMAM_APP_ID, "app_key": EDAMAM_APP_KEY},
    #             json={"title": recipe["title"], "ingr": ingr_strings},
    #         )
    #         data = resp.json()
    #         servings = data.get("yield", 1)
    #         nutrition = {
    #             "calories": round(data["totalNutrients"]["ENERC_KCAL"]["quantity"] / servings),
    #             "protein_g": round(data["totalNutrients"]["PROCNT"]["quantity"] / servings),
    #             "carbs_g": round(data["totalNutrients"]["CHOCDF"]["quantity"] / servings),
    #             "fat_g": round(data["totalNutrients"]["FAT"]["quantity"] / servings),
    #             "fiber_g": round(data["totalNutrients"].get("FIBTG", {}).get("quantity", 0) / servings),
    #         }

    stub_nutrition = [
        {"calories": 420, "protein_g": 45, "carbs_g": 12, "fat_g": 18, "fiber_g": 2},
        {"calories": 510, "protein_g": 38, "carbs_g": 18, "fat_g": 22, "fiber_g": 1},
    ]

    enriched = []
    for i, recipe in enumerate(msg.recipes):
        nutrition = stub_nutrition[i % len(stub_nutrition)]
        score = 100

        if profile.get("daily_calories"):
            target = profile["daily_calories"] / 3
            score -= min(abs(nutrition["calories"] - target) / 8, 30)

        if profile.get("protein_g"):
            target = profile["protein_g"] / 3
            score -= min(abs(nutrition["protein_g"] - target) * 1.5, 20)

        for pref in profile.get("cuisine_preferences", []):
            if any(pref.lower() in t.lower() for t in recipe.get("tags", [])):
                score += 15

        for restriction in profile.get("dietary_restrictions", []):
            if restriction.lower() in ["vegan", "vegetarian"]:
                if any(t in recipe.get("tags", []) for t in ["seafood", "chicken", "meat"]):
                    score -= 100

        reasons = []
        if nutrition["protein_g"] >= 30:
            reasons.append("High protein per serving")
        for pref in profile.get("cuisine_preferences", []):
            if any(pref.lower() in t.lower() for t in recipe.get("tags", [])):
                reasons.append(f"Matches {pref} cuisine preference")
        if not reasons:
            reasons.append("Good overall nutritional balance")

        enriched.append({
            **recipe,
            "nutrition_per_serving": nutrition,
            "match_score": max(0, min(100, round(score))),
            "match_reasons": reasons,
        })

    enriched.sort(key=lambda r: r["match_score"], reverse=True)
    ctx.logger.info(f"Matched and ranked {len(enriched)} recipes")
    await ctx.send(sender, MatchResult(matched_recipes=enriched))


# ---------------------------------------------------------------------------
# Agent 3 — Meal Planner
# Scales recipes and builds shopping list
# ---------------------------------------------------------------------------

planner = Agent(
    name="planner_agent",
    seed=PLANNER_SEED,
    port=8003,
    endpoint=["http://localhost:8003/submit"],
)

@planner.on_event("startup")
async def planner_startup(ctx: Context):
    ctx.logger.info(f"Planner agent started — address: {planner.address}")

@planner.on_message(model=PlanRequest, replies=PlanResult)
async def handle_plan(ctx: Context, sender: str, msg: PlanRequest):
    profile = msg.profile
    top = msg.matched_recipes[:3]
    servings_needed = profile.get("meal_prep_servings", 4)
    budget = profile.get("weekly_budget_usd")

    meal_plan = []
    shopping: dict[str, dict] = {}

    for recipe in top:
        scale = servings_needed / recipe["servings"]
        scaled_ings = []
        for ing in recipe["ingredients"]:
            sa = round(ing["amount"] * scale, 2)
            scaled_ings.append({**ing, "amount": sa})
            key = ing["name"].lower()
            if key not in shopping:
                shopping[key] = {"name": ing["name"], "amount": sa, "unit": ing["unit"]}
            else:
                shopping[key]["amount"] = round(shopping[key]["amount"] + sa, 2)

        meal_plan.append({
            **recipe,
            "scaled_servings": servings_needed,
            "scaled_ingredients": scaled_ings,
        })

    est_cost = round(servings_needed * len(top) * 2.1, 2)

    # TODO: Instacart API integration
    # POST https://connect.instacart.com/v2/fulfillment/orders
    # Headers: Authorization: Bearer {INSTACART_API_KEY}

    result = {
        "meal_plan": meal_plan,
        "shopping_list": list(shopping.values()),
        "estimated_weekly_cost_usd": est_cost,
        "within_budget": est_cost <= budget if budget else None,
        "instacart_order_url": None,
    }

    ctx.logger.info(f"Meal plan built — {len(meal_plan)} meals, est. ${est_cost}")
    await ctx.send(sender, PlanResult(meal_plan=result))


# ---------------------------------------------------------------------------
# Orchestrator — chains all 3 agents together
# ---------------------------------------------------------------------------

orchestrator = Agent(
    name="orchestrator",
    seed=ORCH_SEED,
    port=8004,
    endpoint=["http://localhost:8004/submit"],
)

SCRAPER_ADDR = scraper.address
MATCHER_ADDR = matcher.address
PLANNER_ADDR = planner.address

class PipelineRequest(Model):
    profile: dict

class PipelineResult(Model):
    result: dict

@orchestrator.on_event("startup")
async def orch_startup(ctx: Context):
    ctx.logger.info(f"Orchestrator started — address: {orchestrator.address}")
    ctx.logger.info(f"  Scraper:  {SCRAPER_ADDR}")
    ctx.logger.info(f"  Matcher:  {MATCHER_ADDR}")
    ctx.logger.info(f"  Planner:  {PLANNER_ADDR}")

@orchestrator.on_message(model=PipelineRequest, replies=PipelineResult)
async def start_pipeline(ctx: Context, sender: str, msg: PipelineRequest):
    ctx.storage.set("original_sender", sender)
    ctx.storage.set("profile", msg.profile)
    ctx.logger.info("Pipeline started — sending to Scraper")
    await ctx.send(
        SCRAPER_ADDR,
        ScrapeRequest(substack_url=msg.profile.get("substack_url", "https://nicolerucker.substack.com"))
    )

@orchestrator.on_message(model=ScrapeResult)
async def on_scraped(ctx: Context, sender: str, msg: ScrapeResult):
    profile = ctx.storage.get("profile")
    ctx.logger.info(f"Scrape done — {len(msg.recipes)} recipes. Sending to Matcher")
    await ctx.send(MATCHER_ADDR, MatchRequest(recipes=msg.recipes, profile=profile))

@orchestrator.on_message(model=MatchResult)
async def on_matched(ctx: Context, sender: str, msg: MatchResult):
    profile = ctx.storage.get("profile")
    ctx.logger.info(f"Match done — sending top {len(msg.matched_recipes)} to Planner")
    await ctx.send(PLANNER_ADDR, PlanRequest(matched_recipes=msg.matched_recipes, profile=profile))

@orchestrator.on_message(model=PlanResult)
async def on_planned(ctx: Context, sender: str, msg: PlanResult):
    original_sender = ctx.storage.get("original_sender")
    ctx.logger.info("Plan done — pipeline complete")
    await ctx.send(original_sender, PipelineResult(result=msg.meal_plan))


# ---------------------------------------------------------------------------
# Run all agents together using Bureau
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bureau = Bureau()
    bureau.add(scraper)
    bureau.add(matcher)
    bureau.add(planner)
    bureau.add(orchestrator)
    print("Starting sauced.ai agent bureau...")
    print(f"  Scraper address:       {scraper.address}")
    print(f"  Matcher address:       {matcher.address}")
    print(f"  Planner address:       {planner.address}")
    print(f"  Orchestrator address:  {orchestrator.address}")
    bureau.run()