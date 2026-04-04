"""
Agent 1 — Scraper Agent
Uses Browser Use to watch a Substack food newsletter and extract recipes.

TODO (Person 2):
  - Install: pip install browser-use
  - Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env for Browser Use's LLM
  - Plug in real scraping logic in `scrape()`
"""

import asyncio
import uuid
from typing import Optional

from models import Recipe, Ingredient

# ── Browser Use import ────────────────────────────────────────────────────────
# Uncomment when ready:
# from browser_use import Agent as BrowserAgent
# from langchain_openai import ChatOpenAI


class ScraperAgent:
    """
    Fetch.AI uAgent wrapper around Browser Use.
    Watches a Substack page and extracts structured recipe data.
    """

    def __init__(self):
        # TODO: init Browser Use LLM
        # self.llm = ChatOpenAI(model="gpt-4o")
        pass

    async def scrape(self, url: str, max_recipes: int = 10) -> list[Recipe]:
        """
        Main entry point. Given a Substack URL, returns up to max_recipes recipes.
        """
        print(f"[ScraperAgent] Starting scrape: {url}")

        # ── STUB: replace with real Browser Use logic ─────────────────────────
        # agent = BrowserAgent(
        #     task=self._build_task(url, max_recipes),
        #     llm=self.llm,
        # )
        # result = await agent.run()
        # return self._parse_result(result)

        await asyncio.sleep(1)  # Simulate async work
        return self._stub_recipes(url, max_recipes)

    def _build_task(self, url: str, max_recipes: int) -> str:
        return f"""
        Go to {url}. This is a food newsletter on Substack.
        Find up to {max_recipes} recipe posts. For each recipe:
        1. Navigate to the recipe post
        2. Extract: title, ingredients (with amounts), instructions, prep/cook time, serving size
        3. Find any image
        4. Return structured data as JSON

        Be thorough — scroll down to load more posts if needed.
        Return ONLY valid JSON, no prose.
        """

    def _parse_result(self, raw: str) -> list[Recipe]:
        """Parse Browser Use output into Recipe models."""
        import json
        try:
            data = json.loads(raw)
            recipes = []
            for item in data.get("recipes", []):
                recipes.append(Recipe(
                    id=str(uuid.uuid4()),
                    title=item.get("title", "Untitled"),
                    source_url=item.get("url", ""),
                    image_url=item.get("image"),
                    description=item.get("description"),
                    ingredients=[
                        Ingredient(
                            name=ing.get("name", ""),
                            amount=ing.get("amount"),
                            unit=ing.get("unit")
                        ) for ing in item.get("ingredients", [])
                    ],
                    instructions=item.get("instructions", []),
                    prep_time_min=item.get("prep_time"),
                    cook_time_min=item.get("cook_time"),
                    servings=item.get("servings"),
                    tags=item.get("tags", []),
                    raw_text=item.get("raw_text"),
                ))
            return recipes
        except Exception as e:
            print(f"[ScraperAgent] Parse error: {e}")
            return []

    # ── STUB DATA (remove when real scraper is ready) ─────────────────────────

    def _stub_recipes(self, url: str, count: int) -> list[Recipe]:
        stubs = [
            {
                "title": "Soy-Glazed Salmon Bowl",
                "description": "A weeknight staple with umami-rich glaze and fluffy jasmine rice.",
                "ingredients": [
                    {"name": "salmon fillet", "amount": "6", "unit": "oz"},
                    {"name": "soy sauce", "amount": "3", "unit": "tbsp"},
                    {"name": "honey", "amount": "1", "unit": "tbsp"},
                    {"name": "jasmine rice", "amount": "1", "unit": "cup"},
                    {"name": "sesame seeds", "amount": "1", "unit": "tsp"},
                ],
                "instructions": [
                    "Cook rice per package instructions.",
                    "Mix soy sauce and honey to make glaze.",
                    "Pan-sear salmon 4 min per side, basting with glaze.",
                    "Serve over rice, sprinkle sesame seeds.",
                ],
                "prep_time": 10, "cook_time": 20, "servings": 2,
                "tags": ["asian", "seafood", "high-protein"],
            },
            {
                "title": "Lemon Herb Roasted Chicken Thighs",
                "description": "Crispy-skinned thighs with bright lemon and fresh herbs. Sheet pan, minimal effort.",
                "ingredients": [
                    {"name": "chicken thighs", "amount": "4", "unit": "pieces"},
                    {"name": "lemon", "amount": "2", "unit": "whole"},
                    {"name": "garlic", "amount": "4", "unit": "cloves"},
                    {"name": "fresh thyme", "amount": "4", "unit": "sprigs"},
                    {"name": "olive oil", "amount": "2", "unit": "tbsp"},
                ],
                "instructions": [
                    "Preheat oven to 425°F.",
                    "Toss chicken with lemon juice, garlic, thyme, oil.",
                    "Roast 35–40 min until skin is crispy.",
                ],
                "prep_time": 10, "cook_time": 40, "servings": 4,
                "tags": ["mediterranean", "high-protein", "sheet-pan"],
            },
            {
                "title": "Black Bean & Sweet Potato Tacos",
                "description": "Smoky, satisfying plant-based tacos ready in 25 minutes.",
                "ingredients": [
                    {"name": "black beans", "amount": "1", "unit": "can"},
                    {"name": "sweet potato", "amount": "2", "unit": "medium"},
                    {"name": "corn tortillas", "amount": "8", "unit": "pieces"},
                    {"name": "cumin", "amount": "1", "unit": "tsp"},
                    {"name": "lime", "amount": "1", "unit": "whole"},
                ],
                "instructions": [
                    "Cube and roast sweet potato at 400°F for 20 min.",
                    "Warm beans with cumin in pan.",
                    "Assemble tacos, squeeze lime over top.",
                ],
                "prep_time": 5, "cook_time": 25, "servings": 4,
                "tags": ["mexican", "vegetarian", "vegan", "budget"],
            },
        ]
        recipes = []
        for i, s in enumerate(stubs[:count]):
            recipes.append(Recipe(
                id=str(uuid.uuid4()),
                title=s["title"],
                source_url=f"{url}/post-{i+1}",
                description=s["description"],
                ingredients=[Ingredient(**ing) for ing in s["ingredients"]],
                instructions=s["instructions"],
                prep_time_min=s["prep_time"],
                cook_time_min=s["cook_time"],
                servings=s["servings"],
                tags=s["tags"],
            ))
        return recipes
